from enum import Enum

common_headers = {
	"Accept": "application/json",
	"Accept-Encoding": "gzip, deflate, br, zstd",
	"Accept-Language": "en-GB,en;q=0.5",
	"Connection": "keep-alive",
	"DNT": "1",
	"Host": "api.mykurve.com",
	"Origin": "https://www.mykurve.com",
	"Referer": "https://www.mykurve.com/",
	"Sec-Fetch-Dest": "empty",
	"Sec-Fetch-Mode": "cors",
	"Sec-Fetch-Site": "same-site",
	"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
	"Content-Type": "application/x-www-form-urlencoded",
}


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
