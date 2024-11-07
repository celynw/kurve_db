#!/usr/bin/env python3
from pathlib import Path

import pandas as pd
import typer
from kellog import debug, error, info, warning
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import sessionmaker as SessionMaker

from kurve_scraper.db.definitions import (
	Base,
	DailyConsumptionAverages,
	DailyMeterReading,
	HourlyMeterReading,
	MonthlyConsumptionAverages,
	MonthlyMeterReading,
	TariffHistory,
	WeeklyConsumptionAverages,
	YearlyConsumptionAverages,
)
from kurve_scraper.db.interactions import get_primary_key_names

# List of SQLAlchemy models to merge
tables = [
	DailyConsumptionAverages,
	DailyMeterReading,
	HourlyMeterReading,
	MonthlyConsumptionAverages,
	MonthlyMeterReading,
	TariffHistory,
	WeeklyConsumptionAverages,
	YearlyConsumptionAverages,
]


def main() -> None:
	output_db = Path("water_usage_merged.db")
	db_paths = [db for db in Path().glob("*.db*") if db != output_db]

	combined_dfs = {k: v for k, v in zip(tables, [pd.DataFrame() for _ in range(len(tables))], strict=False)}

	for i, db_path in enumerate(db_paths):
		engine = create_engine(f"sqlite:///{db_path}", echo=False)
		Base.metadata.create_all(engine)
		Session: SessionMaker = sessionmaker(bind=engine)
		with Session() as session:
			for Table in tables:
				# Set up the table schema using definitions
				table = Table()
				with Session() as session:
					# Get the data from the source database
					query = session.query(table.__table__.columns)
					results = pd.DataFrame(query.all())
					combined_dfs[Table] = pd.concat([combined_dfs[Table], results])

	# Sort combined_dfs by the primary key, then the other columns
	for Table in tables:
		primary_keys = get_primary_key_names(Table)
		other_columns = [col.name for col in Table.__table__.columns if col.name not in primary_keys]
		combined_dfs[Table] = combined_dfs[Table].sort_values(by=primary_keys + other_columns)

	# Drop duplicate entries for primary keys, keeping the rows with the largest values from the other columns
	for Table in tables:
		combined_dfs[Table] = combined_dfs[Table].drop_duplicates(subset=get_primary_key_names(Table), keep="last")

	# Write the combined dataframes to the output database
	output_engine = create_engine(f"sqlite:///{output_db}", echo=False)
	Base.metadata.create_all(output_engine)
	Session: SessionMaker = sessionmaker(bind=output_engine)

	with Session() as session:
		for Table in tables:
			# Create an empty table with primary key definition first
			Table.__table__.create(bind=output_engine, checkfirst=True)
			try:
				session.commit()
			except Exception as e:
				session.rollback()
				raise RuntimeError(f"Failed to commit session: {e}")

			if Table is DailyMeterReading:
				# Drop rows which have "period_start_utc" not at midnight because they're not complete periods
				combined_dfs[Table] = combined_dfs[Table].loc[combined_dfs[Table]["period_start_utc"].dt.hour == 0]

			# Now write the data, appending the empty table
			combined_dfs[Table].to_sql(Table.__tablename__, output_engine, if_exists="append", index=False)


if __name__ == "__main__":
	main()
