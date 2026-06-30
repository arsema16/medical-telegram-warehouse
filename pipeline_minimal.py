"""
Minimal Dagster pipeline with correct op names.
"""

from dagster import job, op, Definitions, ScheduleDefinition


@op
def scrape_telegram_data(context):
    """Scrape data from Telegram channels."""
    context.log.info("📡 Scraping Telegram data...")
    return {"status": "scraped"}


@op
def load_raw_to_postgres(context, scraped_data):
    """Load raw data to PostgreSQL."""
    context.log.info("📊 Loading data to PostgreSQL...")
    return {"status": "loaded"}


@op
def run_dbt_transformations(context, loaded_data):
    """Run dbt transformations."""
    context.log.info("🔧 Running dbt transformations...")
    return {"status": "transformed"}


@op
def run_yolo_enrichment(context, dbt_data):
    """Run YOLO object detection."""
    context.log.info("🖼️ Running YOLO enrichment...")
    return {"status": "enriched"}


@job
def medical_telegram_pipeline():
    """Complete medical telegram pipeline."""
    scraped = scrape_telegram_data()
    loaded = load_raw_to_postgres(scraped)
    dbt_result = run_dbt_transformations(loaded)
    yolo_result = run_yolo_enrichment(dbt_result)
    return yolo_result


# Daily schedule at 9:00 AM
daily_schedule = ScheduleDefinition(
    job=medical_telegram_pipeline,
    cron_schedule="0 9 * * *",
    name="daily_medical_pipeline",
)

defs = Definitions(
    jobs=[medical_telegram_pipeline],
    schedules=[daily_schedule],
)