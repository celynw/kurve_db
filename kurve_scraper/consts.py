from enum import Enum


class PeriodType(Enum):
	"""
	Period types for the consumption tab in the Kurve web app.

	Note: The consumption tab has categories for "Daily", "Weekly", "Monthly", and "Yearly".
	The data itself for Daily is the hourly data for each day.
	The data for Weekly is the daily data for each week.
	The data for Monthly is the daily data for each month, just shown in a different view.
	The data for Yearly is the daily data for each month.
	"""

	HOURLY = "Day"
	DAILY = "Week"  # NOTE: The data is the same as "Month"
	WEEKLY = "Month"  # NOTE: The data is the same as "Week"
	MONTHLY = "Year"
