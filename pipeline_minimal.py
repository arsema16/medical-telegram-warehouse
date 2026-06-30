"""
Minimal Dagster pipeline - Just runs all scripts.
"""

import sys
import subprocess
from pathlib import Path
from dagster import job, op, Definitions

sys.path.insert(0, str(Path(__file__).parent))

@op
def run_all(context):
    """Run all pipeline steps."""
    context.log.info("🚀 Starting complete pipeline...")
    
    steps = [
        ("Scraping", "scripts/run_scraper.py"),
        ("Loading", "scripts/run_loader.py"),
        ("dbt", "medical_warehouse/dbt run"),
        ("YOLO", "scripts/run_yolo.py"),
    ]
    
    for name, script in steps:
        context.log.info(f"▶️ Running {name}...")
        try:
            result = subprocess.run(
                [sys.executable, script] if script.endswith('.py') else script.split(),
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent)
            )
            if result.returncode == 0:
                context.log.info(f"✅ {name} completed")
            else:
                context.log.warning(f"⚠️ {name} had issues")
        except Exception as e:
            context.log.error(f"❌ {name} failed: {e}")
    
    context.log.info("🎉 Pipeline complete!")
    return "done"

@job
def minimal_pipeline():
    """Minimal pipeline."""
    run_all()

defs = Definitions(jobs=[minimal_pipeline])