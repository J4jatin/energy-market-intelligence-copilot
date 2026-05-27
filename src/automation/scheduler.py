"""
Automated scheduler for the Market Intelligence pipeline.
Runs daily at 07:00 and can be triggered manually.

Usage:
    python src/automation/scheduler.py              # Start scheduler daemon
    python src/automation/scheduler.py --run-now    # Run pipeline immediately
"""

import argparse
import logging
import time
from datetime import datetime

import schedule

from src.automation.pipeline import MarketIntelligencePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Job function called by scheduler."""
    logger.info(f"⏰ Scheduled run triggered at {datetime.now().strftime('%H:%M:%S')}")
    pipeline = MarketIntelligencePipeline()
    result = pipeline.run()

    if result["status"] == "completed":
        logger.info(
            f"✅ Done — {result['articles_processed']} articles, "
            f"{result['duration_seconds']}s"
        )
    else:
        logger.error(f"❌ Pipeline failed: {result.get('errors')}")


def start_scheduler(run_time: str = "07:00"):
    """Start the daily scheduler daemon."""
    logger.info(f"🗓  Scheduler started — pipeline runs daily at {run_time}")
    logger.info("   Press Ctrl+C to stop")

    schedule.every().day.at(run_time).do(run_pipeline)

    # Also run weekly full refresh on Mondays
    schedule.every().monday.at("06:30").do(
        lambda: logger.info("📅 Monday full refresh scheduled")
    )

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market Intelligence Scheduler")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the pipeline immediately instead of scheduling",
    )
    parser.add_argument(
        "--time",
        type=str,
        default="07:00",
        help="Daily run time in HH:MM format (default: 07:00)",
    )
    args = parser.parse_args()

    if args.run_now:
        logger.info("▶️  Running pipeline immediately...")
        run_pipeline()
    else:
        start_scheduler(run_time=args.time)
