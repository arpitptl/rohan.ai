from services.backfill_historical_data import GenerateHistoricalData
from utils.logger import logger
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate historical FIP metrics JSON file.")
    parser.add_argument("--days", type=int, default=30, help="Number of days back to generate")
    parser.add_argument("--interval", type=int, default=15, help="Interval in minutes between points")
    parser.add_argument("--output", type=str, default="fip_metrics_historical.json", help="Output JSON file path")
    args = parser.parse_args()

    gen = GenerateHistoricalData()
    gen.export_to_file(days_back=args.days, interval_minutes=args.interval, output_file=args.output)
    logger.info(f"Historical metrics JSON generated at {args.output}")

if __name__ == "__main__":
    main() 