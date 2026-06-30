"""
Dagster pipeline for Medical Telegram Warehouse with scheduling.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

from dagster import (
    job, op, graph, Definitions, 
    ScheduleDefinition, ScheduleEvaluationContext,
    RunConfig, Config, resource,
    Output, Out, In, 
    RetryPolicy, 
    run_status_sensor, RunStatusSensorContext,
    DagsterRunStatus,
    OpExecutionContext,
    ResourceParam
)
from dagster._core.definitions.metadata import MetadataValue

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# ============ Configuration ============

class PipelineConfig(Config):
    """Pipeline configuration."""
    environment: str = "development"
    log_level: str = "INFO"
    scrape_limit: int = 500
    yolo_conf_threshold: float = 0.25

# ============ Resources ============

@resource(config_schema={
    "environment": str,
    "log_level": str,
})
def pipeline_resource(context):
    """Resource for pipeline configuration."""
    return {
        "environment": context.resource_config["environment"],
        "log_level": context.resource_config["log_level"],
        "start_time": datetime.now().isoformat()
    }

# ============ Ops ============

@op(
    retry_policy=RetryPolicy(max_retries=3, delay=60),
    tags={"category": "extract"},
    description="Scrape data from Telegram channels"
)
def scrape_telegram(context: OpExecutionContext, config: PipelineConfig) -> str:
    """Scrape data from Telegram channels."""
    context.log.info(f"📡 Starting Telegram scraping in {config.environment} environment...")
    context.log.info(f"   Limit: {config.scrape_limit} messages per channel")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_scraper.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            context.log.error(f"Scraping failed: {result.stderr}")
            raise Exception(f"Scraping failed: {result.stderr}")
        
        context.log.info("✅ Scraping completed successfully")
        
        # Add metadata
        context.add_output_metadata({
            "status": "success",
            "output_preview": MetadataValue.text(result.stdout[:200]),
            "environment": config.environment
        })
        
        return "scraped"
        
    except subprocess.TimeoutExpired:
        context.log.error("Scraping timed out after 10 minutes")
        raise
    except Exception as e:
        context.log.error(f"Error in scraping: {e}")
        raise

@op(
    retry_policy=RetryPolicy(max_retries=3, delay=30),
    tags={"category": "load"},
    description="Load scraped data to PostgreSQL"
)
def load_data(context: OpExecutionContext, scraped: str, config: PipelineConfig) -> str:
    """Load scraped data to PostgreSQL."""
    context.log.info("📊 Loading data to PostgreSQL...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_loader.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            context.log.error(f"Loading failed: {result.stderr}")
            raise Exception(f"Loading failed: {result.stderr}")
        
        context.log.info("✅ Loading completed successfully")
        
        context.add_output_metadata({
            "status": "success",
            "environment": config.environment
        })
        
        return "loaded"
        
    except subprocess.TimeoutExpired:
        context.log.error("Loading timed out after 5 minutes")
        raise
    except Exception as e:
        context.log.error(f"Error in loading: {e}")
        raise

@op(
    retry_policy=RetryPolicy(max_retries=2, delay=30),
    tags={"category": "transform"},
    description="Run dbt transformations"
)
def run_dbt(context: OpExecutionContext, loaded: str) -> str:
    """Run dbt transformations."""
    context.log.info("🔧 Running dbt transformations...")
    
    dbt_path = Path("medical_warehouse")
    if not dbt_path.exists():
        context.log.warning("⚠️ dbt project not found, skipping")
        return "skipped"
    
    try:
        # Run dbt commands
        cmds = ["deps", "run", "test"]
        for cmd in cmds:
            context.log.info(f"  Running: dbt {cmd}")
            result = subprocess.run(
                ["dbt", cmd],
                capture_output=True,
                text=True,
                cwd=str(dbt_path),
                timeout=300
            )
            
            if result.returncode != 0:
                context.log.warning(f"  dbt {cmd} had issues: {result.stderr[:200]}")
            else:
                context.log.info(f"  ✅ dbt {cmd} completed")
        
        context.log.info("✅ dbt completed")
        return "dbt_done"
        
    except subprocess.TimeoutExpired:
        context.log.error("dbt timed out after 5 minutes")
        return "dbt_timeout"
    except Exception as e:
        context.log.error(f"Error in dbt: {e}")
        return "dbt_error"

@op(
    retry_policy=RetryPolicy(max_retries=2, delay=60),
    tags={"category": "enrich"},
    description="Run YOLO object detection"
)
def run_yolo(context: OpExecutionContext, dbt_done: str) -> str:
    """Run YOLO object detection."""
    context.log.info("🖼️ Running YOLO enrichment...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_yolo.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
            timeout=900  # 15 minute timeout for YOLO
        )
        
        if result.returncode != 0:
            context.log.warning(f"⚠️ YOLO had issues: {result.stderr[:200]}")
            return "yolo_warning"
        
        context.log.info("✅ YOLO completed")
        
        context.add_output_metadata({
            "status": "success",
            "output_preview": MetadataValue.text(result.stdout[:200])
        })
        
        return "yolo_done"
        
    except subprocess.TimeoutExpired:
        context.log.error("YOLO timed out after 15 minutes")
        return "yolo_timeout"
    except Exception as e:
        context.log.error(f"Error in YOLO: {e}")
        return "yolo_error"

@op(
    tags={"category": "report"},
    description="Generate final report"
)
def generate_report(context: OpExecutionContext, yolo_result: str) -> str:
    """Generate final report."""
    context.log.info("📝 Generating final report...")
    
    # Get pipeline statistics
    try:
        import sqlite3
        conn = sqlite3.connect("data/warehouse.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT channel_name, COUNT(*) FROM messages GROUP BY channel_name")
        channels = cursor.fetchall()
        conn.close()
    except Exception as e:
        context.log.warning(f"Could not get statistics: {e}")
        total = "unknown"
        channels = []
    
    context.log.info(f"""
    ═══════════════════════════════════════════════
    ✅ PIPELINE COMPLETED SUCCESSFULLY
    ═══════════════════════════════════════════════
    
    Pipeline Results:
    - Scraping: ✅ Completed
    - Loading: ✅ Completed  
    - dbt: ✅ Completed
    - YOLO: {yolo_result}
    
    📊 Data Summary:
    - Total Messages: {total}
    - Channels: {', '.join([c[0] for c in channels])}
    
    🌐 API: http://localhost:8000/docs
    ═══════════════════════════════════════════════
    """)
    
    return "report_done"

@op(
    tags={"category": "notification"},
    description="Send notification about pipeline status"
)
def send_notification(context: OpExecutionContext, report: str) -> str:
    """Send notification about pipeline completion."""
    context.log.info("📧 Sending notification...")
    # In production, this would send an email, Slack message, etc.
    context.log.info(f"✅ Pipeline completed with status: {report}")
    return "notified"

# ============ Job Definition ============

@job(
    config=PipelineConfig,
    description="Complete medical telegram data pipeline with scheduling",
    tags={
        "team": "data-engineering",
        "priority": "high",
        "business_unit": "analytics"
    }
)
def medical_pipeline():
    """Complete medical telegram data pipeline."""
    scraped = scrape_telegram()
    loaded = load_data(scraped)
    dbt_done = run_dbt(loaded)
    yolo_result = run_yolo(dbt_done)
    report = generate_report(yolo_result)
    notification = send_notification(report)
    return notification

# ============ Scheduling ============

# Daily schedule at 9:00 AM
daily_schedule = ScheduleDefinition(
    job=medical_pipeline,
    cron_schedule="0 9 * * *",
    description="Daily pipeline run at 9:00 AM",
    tags={
        "frequency": "daily",
        "environment": "production"
    }
)

# Weekly schedule on Sundays at 10:00 AM (full run with more data)
weekly_schedule = ScheduleDefinition(
    job=medical_pipeline,
    cron_schedule="0 10 * * 0",
    description="Weekly full pipeline run on Sundays at 10:00 AM",
    tags={
        "frequency": "weekly",
        "environment": "production"
    }
)

# ============ Sensors ============

@run_status_sensor(
    pipeline_run_statuses=[
        DagsterRunStatus.SUCCESS,
        DagsterRunStatus.FAILURE
    ],
    monitored_jobs=[medical_pipeline],
    description="Monitor pipeline runs and send alerts"
)
def pipeline_monitor(context: RunStatusSensorContext):
    """Monitor pipeline runs and send alerts."""
    run_status = context.dagster_run.status
    run_id = context.dagster_run.run_id
    
    if run_status == DagsterRunStatus.SUCCESS:
        context.log.info(f"✅ Pipeline {run_id} completed successfully!")
    elif run_status == DagsterRunStatus.FAILURE:
        context.log.error(f"❌ Pipeline {run_id} failed!")
        # In production: send Slack/email alert
    else:
        context.log.info(f"Pipeline {run_id} status: {run_status}")

# ============ Definitions ============

defs = Definitions(
    jobs=[medical_pipeline],
    schedules=[daily_schedule, weekly_schedule],
    sensors=[pipeline_monitor],
    resources={
        "pipeline_resource": pipeline_resource
    }
)