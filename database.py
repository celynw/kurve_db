from abc import ABC
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from consts import PeriodType


class PeriodType(Enum):
	DAILY = "Day"
	WEEKLY = "Week"
	MONTHLY = "Month"
	YEARLY = "Year"


Base = declarative_base()


class MeterReading(Base, ABC):
	id = Column(Integer, primary_key=True, autoincrement=True)
	meter_serial = Column(String, nullable=False)
	period_start_utc = Column(DateTime, nullable=False)
	read_time_utc = Column(DateTime, nullable=False)
	actual_value = Column(Float, nullable=False)
	consumption_value = Column(Float, nullable=False)
	consumption_cost = Column(Float, nullable=False)
	standing_charge = Column(Float, nullable=False)


class DailyMeterReading(MeterReading):
	__tablename__ = "daily_meter_readings"


class WeeklyMeterReading(MeterReading):
	__tablename__ = "weekly_meter_readings"


class MonthlyMeterReading(MeterReading):
	__tablename__ = "monthly_meter_readings"


class YearlyMeterReading(MeterReading):
	__tablename__ = "yearly_meter_readings"


# Connect to SQLite
engine = create_engine("sqlite:///water_usage.db", echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


# Function to check if a reading already exists in the database
def reading_exists(session, meter_serial, period_start_utc):
	return (
		session.query(DailyMeterReading).filter_by(meter_serial=meter_serial, period_start_utc=period_start_utc).first()
		is not None
	)


# Main function to store data in the database
def store_meter_readings(data: dict):
	if not data:
		print("No data to store!")
		return

	meter_serial = data["consumptionMeter"]["meterSerial"]
	readings = data["consumptionMeter"]["pagedMeterReadings"]

	for reading in readings:
		period_start_utc = datetime.fromisoformat(reading["periodStartUTC"].replace("Z", "+00:00"))
		read_time_utc = datetime.fromisoformat(reading["readTimeUTC"].replace("Z", "+00:00"))

		if not reading_exists(session, meter_serial, period_start_utc):
			new_reading = DailyMeterReading(
				meter_serial=meter_serial,
				period_start_utc=period_start_utc,
				read_time_utc=read_time_utc,
				actual_value=reading["actualValue"],
				consumption_value=reading["consumptionValue"],
				consumption_cost=reading["consumptionCost"],
				standing_charge=reading["standingCharge"],
			)
			session.add(new_reading)
			print(f"Added reading for {meter_serial} on {period_start_utc} to the database.")
		else:
			print(f"Reading for {meter_serial} on {period_start_utc} already exists in the database.")

	session.commit()
