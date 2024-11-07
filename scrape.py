#!/usr/bin/env python3

import requests
import typer
from kellog import debug, error, info, warning

from kurve_scraper.api import get_account, get_token
from kurve_scraper.consts import PeriodType, common_headers
from kurve_scraper.db.interactions import (
	store_consumption_averages,
	store_meter_readings,
	store_tariff_history,
)


def main(account_number: int, token: str) -> None:
	headers = common_headers.copy()
	headers["Authorization"] = f"Bearer {token}"
	headers["Priority"] = "u=0"

	period_ranges = {
		PeriodType.HOURLY: (-6, 1),
		PeriodType.DAILY: (-3, 1),
		PeriodType.WEEKLY: (-5, 1),
		PeriodType.MONTHLY: (-2, 1),
	}
	for period_type, period_range in period_ranges.items():
		for page in range(*period_range):
			url = f"https://api.mykurve.com/api/Pages/ConsumptionGraphV2?accountNumber={account_number}&timeRange={period_type.value}&page={page}"

			response = requests.get(url, headers=headers, timeout=3)

			if response.status_code == 200:
				data = response.json()  # Assuming it's JSON data
				store_meter_readings(period_type=period_type, data=data)
				try:
					store_consumption_averages(period_type=period_type, data=data)
				except IndexError:
					warning(f"No data for {period_type} {period_range}")
					continue
			else:
				raise RuntimeError(f"Failed to retrieve data: {response.status_code}")

	store_tariff_history(data)


if __name__ == "__main__":
	username = ""
	password = ""
	cookie = ""

	info("Getting token...")
	token = get_token(username=username, password=password, cookie=cookie)
	debug(f"token: {token}")
	info("Getting account...")
	account_number = get_account(token=token)
	debug(f"account_number: {account_number}")

	main(account_number=account_number, token=token)
