from datetime import datetime

from inflection import underscore
from kellog import debug, error, info, warning
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import sessionmaker as SessionMaker

from kurve_scraper.consts import PeriodType
from kurve_scraper.db.definitions import (
	Base,
	DailyConsumptionAverages,
	DailyMeterReading,
	HourlyMeterReading,
	MeterReading,
	MonthlyConsumptionAverages,
	MonthlyMeterReading,
	TariffHistory,
	WeeklyConsumptionAverages,
	YearlyConsumptionAverages,
)

# Connect to SQLite
engine = create_engine("sqlite:///water_usage.db", echo=False)
Base.metadata.create_all(engine)
Session: SessionMaker = sessionmaker(bind=engine)


# Function to get the primary key column(s) for a table
# def get_primary_key(table_name, cursor: sqlite3.Cursor) -> list[str]:
def get_primary_key_names(table: MeterReading) -> list[str]:
	primary_keys = table.__table__.primary_key.columns.values()

	return [pk.name for pk in primary_keys]


def store_meter_readings(period_type: PeriodType, data: dict) -> None:
	if not data:
		print("No data to store!")
		return

	meter_serial = data["consumptionMeter"]["meterSerial"]
	readings = data["consumptionMeter"]["pagedMeterReadings"]

	match period_type:
		case PeriodType.HOURLY:
			Model = HourlyMeterReading
		case PeriodType.DAILY:
			Model = DailyMeterReading
		case PeriodType.WEEKLY:
			return  # Redundant: Weekly ("Month") data is the same as Daily ("Week") data
		case PeriodType.MONTHLY:
			Model = MonthlyMeterReading
		case _:
			raise ValueError(f"Unsupported period type: {period_type}")

	with Session() as session:
		for reading in readings:
			period_start_utc = datetime.fromisoformat(reading["periodStartUtc"].replace("Z", "+00:00"))
			read_time_utc = datetime.fromisoformat(reading["readTimeUtc"].replace("Z", "+00:00"))

			existing = session.query(Model).filter_by(period_start_utc=period_start_utc).first()
			if existing:
				info(f"{period_type.value} reading for {period_start_utc} already exists in the database")
				# Check if data is different and display a warning if needed
				for key, value in reading.items():
					existing_value = getattr(existing, underscore(key))

					if isinstance(existing_value, datetime) and isinstance(value, str):
						value = datetime.fromisoformat(value).replace(tzinfo=None)

					if existing_value != value:
						if value > existing_value:
							# Replace with the new data
							setattr(existing, underscore(key), value)
							debug(
								f"Replacing value for {Model.__tablename__} at {period_start_utc}: "
								f"'{key}' {existing_value} -> {value}",
							)
						else:
							warning(
								f"Data mismatch for {Model.__tablename__} at {period_start_utc}: "
								f"'{key}' {existing_value} -> {value}",
							)
			else:
				new_reading = Model(
					meter_serial=meter_serial,
					period_start_utc=period_start_utc,
					read_time_utc=read_time_utc,
					actual_value=reading["actualValue"],
					consumption_value=reading["consumptionValue"],
					consumption_cost=reading["consumptionCost"],
					standing_charge=reading["standingCharge"],
				)
				session.add(new_reading)
				info(f"{period_type.value} reading stored for {period_start_utc}")

		try:
			session.commit()
		except Exception as e:
			session.rollback()
			raise RuntimeError(f"Failed to commit session: {e}")


def store_consumption_averages(period_type: PeriodType, data: dict) -> None:
	period = datetime.fromisoformat(data["consumptionMeter"]["pagedMeterReadings"][0]["periodStartUtc"])
	averages = data["consumptionAverages"]

	match period_type:
		case PeriodType.HOURLY:
			Model = DailyConsumptionAverages
		case PeriodType.DAILY:
			Model = WeeklyConsumptionAverages
		case PeriodType.WEEKLY:
			Model = MonthlyConsumptionAverages
		case PeriodType.MONTHLY:
			Model = YearlyConsumptionAverages
		case _:
			raise ValueError(f"Unsupported period type: {period_type}")

	with Session() as session:
		try:
			existing = session.query(Model).filter_by(period=period).first()
			if existing:
				info(f"{period_type.value} reading for {period} already exists in the database")
				# Check if data is different and display a warning if needed
				for key, value in averages.items():
					existing_value = getattr(existing, underscore(key))

					if isinstance(existing_value, datetime) and isinstance(value, str):
						value = datetime.fromisoformat(value).replace(tzinfo=None)

					if value != existing_value:
						if value > existing_value:
							# Replace with the new data
							setattr(existing, underscore(key), value)
							debug(
								f"Replacing value for {Model.__tablename__} at {period}: "
								f"'{key}' {existing_value} -> {value}",
							)
						else:
							warning(
								f"Data mismatch for {Model.__tablename__} at {period}: "
								f"'{key}' {existing_value} -> {value}",
							)
			else:
				new_averages = Model(
					period=period,
					daily_cost=averages["dailyCost"],
					daily_usage=averages["dailyUsage"],
					weekly_cost=averages.get("weeklyCost"),
					weekly_usage=averages.get("weeklyUsage"),
					monthly_cost=averages.get("monthlyCost"),
					monthly_usage=averages.get("monthlyUsage"),
				)
				session.add(new_averages)
				info(f"{period_type.value} consumption average stored for {period}")
		except IndexError:
			warning(f"Couldn't find consumption for {Model.__name__}: {data}")
		else:
			try:
				session.commit()
			except Exception as e:
				session.rollback()
				raise RuntimeError(f"Failed to commit session: {e}")


def store_tariff_history(data: dict) -> None:
	tariffs = data["tariffHistory"]["tariffs"]
	current_tariff = data["tariffHistory"]["tariffInForceNow"]

	with Session() as session:
		for tariff in tariffs:
			existing = session.query(TariffHistory).filter_by(tariff_id=tariff["tariffId"]).first()
			if not existing:
				new_tariff = TariffHistory(
					tariff_id=tariff["tariffId"],
					consumer_number=tariff["consumerNumber"],
					pricing_plan_code=tariff["pricingPlanCode"],
					pricing_plan_description=tariff["pricingPlanDescription"],
					rate=tariff["rate"],
					standing_charge=tariff["standingCharge"],
					tariff_change_date=datetime.fromisoformat(tariff["tariffChangeDate"].replace("Z", "+00:00")),
					is_current=False,
				)
				session.add(new_tariff)

		current_existing = session.query(TariffHistory).filter_by(tariff_id=current_tariff["tariffId"]).first()
		if not current_existing:
			new_current_tariff = TariffHistory(
				tariff_id=current_tariff["tariffId"],
				consumer_number=current_tariff["consumerNumber"],
				pricing_plan_code=current_tariff["pricingPlanCode"],
				pricing_plan_description=current_tariff["pricingPlanDescription"],
				rate=current_tariff["rate"],
				standing_charge=current_tariff["standingCharge"],
				tariff_change_date=datetime.fromisoformat(current_tariff["tariffChangeDate"].replace("Z", "+00:00")),
				is_current=True,
			)
			session.add(new_current_tariff)
		else:
			current_existing.is_current = True  # Update to reflect it's the active tariff

		try:
			session.commit()
		except Exception as e:
			session.rollback()
			raise RuntimeError(f"Failed to commit session: {e}")
