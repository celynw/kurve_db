from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MeterReading(Base):
	__abstract__ = True
	meter_serial = Column(String, nullable=False)
	period_start_utc = Column(DateTime, primary_key=True, unique=True)
	read_time_utc = Column(DateTime, nullable=False)
	actual_value = Column(Float, nullable=False)
	consumption_value = Column(Float, nullable=False)
	consumption_cost = Column(Float, nullable=False)
	standing_charge = Column(Float, nullable=False)


class HourlyMeterReading(MeterReading):
	__tablename__ = "hourly_meter_readings"


class DailyMeterReading(MeterReading):
	__tablename__ = "daily_meter_readings"


class MonthlyMeterReading(MeterReading):
	__tablename__ = "monthly_meter_readings"


class TariffHistory(Base):
	__tablename__ = "tariff_history"
	id = Column(Integer, primary_key=True, autoincrement=True)
	tariff_id = Column(Integer, nullable=False)
	consumer_number = Column(String, nullable=False)
	pricing_plan_code = Column(String, nullable=False)
	pricing_plan_description = Column(String, nullable=False)
	rate = Column(Float, nullable=False)
	standing_charge = Column(Float, nullable=False)
	tariff_change_date = Column(DateTime, nullable=False)
	is_current = Column(Boolean, default=False)  # To indicate if this is the currently active tariff


class ConsumptionAverages(Base):
	__abstract__ = True
	period = Column(DateTime, primary_key=True, unique=True)
	daily_cost = Column(Float, nullable=True)
	daily_usage = Column(Float, nullable=True)
	weekly_cost = Column(Float, nullable=True)
	weekly_usage = Column(Float, nullable=True)
	monthly_cost = Column(Float, nullable=True)
	monthly_usage = Column(Float, nullable=True)


class DailyConsumptionAverages(ConsumptionAverages):
	__tablename__ = "daily_consumption_averages"


class WeeklyConsumptionAverages(ConsumptionAverages):
	__tablename__ = "weekly_consumption_averages"


class MonthlyConsumptionAverages(ConsumptionAverages):
	__tablename__ = "monthly_consumption_averages"


class YearlyConsumptionAverages(ConsumptionAverages):
	__tablename__ = "yearly_consumption_averages"
