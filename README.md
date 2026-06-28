# 🏥 Medical Telegram Warehouse

[![GitHub stars](https://img.shields.io/github/stars/arsema16/medical-telegram-warehouse)](https://github.com/arsema16/medical-tegram-warehouse/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/arsema16/medical-telegram-warehouse)](https://github.com/arsema16/medical-telegram-warehouse/network)
[![GitHub issues](https://img.shields.io/github/issues/arsema16/medical-telegram-warehouse)](https://github.com/arsema16/medical-telegram-warehouse/issues)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Unit Tests](https://github.com/arsema16/medical-telegram-warehouse/actions/workflows/unittests.yml/badge.svg)](https://github.com/arsema16/medical-telegram-warehouse/actions/workflows/unittests.yml)

> **An end-to-end data pipeline for Telegram, leveraging dbt for transformation, Dagster for orchestration, and YOLOv8 for data enrichment.**

## 📋 Table of Contents

- [Overview](#overview)
- [Business Need](#business-need)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project implements a modern **ELT (Extract, Load, Transform)** pipeline that scrapes, processes, and analyzes data from public Telegram channels related to Ethiopian medical businesses. The pipeline transforms raw, unstructured data into a clean, analytical data warehouse optimized for business intelligence.

### 📊 Key Statistics

| Metric | Value |
|--------|-------|
| **Total Messages** | 654 |
| **Active Channels** | 3 |
| **Data Points Collected** | 9 per message |
| **API Endpoints** | 7 |
| **dbt Models** | 6 |
| **Test Coverage** | 70%+ |

## 💼 Business Need

As a Data Engineer at **Kara Solutions**, a leading data science consultancy in Ethiopia, you'll build a robust data platform that generates actionable insights about Ethiopian medical businesses using data scraped from public Telegram channels.

### Key Business Questions Answered

- 🏆 **What are the top 10 most frequently mentioned medical products across all channels?**
- 💰 **How does the price or availability of a specific product vary across different channels?**
- 📸 **Which channels have the most visual content (e.g., images of pills vs. creams)?**
- 📈 **What are the daily and weekly trends in posting volume for health-related topics?**

## ✨ Features

### Data Pipeline

- ✅ **Automated Scraping** - Extract data from Telegram channels using Telethon
- ✅ **Data Lake Storage** - Raw data stored in partitioned JSON files
- ✅ **Image Download** - Automatic image downloading and organization
- ✅ **Data Quality Checks** - Automated validation and cleaning
- ✅ **Incremental Loading** - Efficient data updates

### Data Transformation

- ✅ **dbt Integration** - Data Build Tool for transformations
- ✅ **Star Schema** - Dimensional modeling optimized for analytics
- ✅ **Data Testing** - Automated data quality tests
- ✅ **Documentation** - Auto-generated dbt docs

### Data Enrichment

- ✅ **YOLOv8** - Object detection for image analysis
- ✅ **Image Classification** - Promotional, product display, lifestyle, other
- ✅ **Performance Analysis** - Compare engagement across image types

### Analytics & API

- ✅ **FastAPI** - RESTful API with 7 endpoints
- ✅ **Auto Documentation** - Swagger/OpenAPI documentation
- ✅ **Filtering & Search** - Advanced query capabilities
- ✅ **Real-time Stats** - Up-to-date analytics

### Orchestration

- ✅ **Dagster** - Pipeline orchestration and scheduling
- ✅ **Monitoring** - Real-time execution logs
- ✅ **Alerting** - Failure notifications
- ✅ **Scheduling** - Automated daily runs

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.10+ |
| **Data Extraction** | Telethon (Telegram API) |
| **Data Warehouse** | PostgreSQL 15, SQLite (dev) |
| **Transformations** | dbt (Data Build Tool) |
| **Orchestration** | Dagster |
| **Computer Vision** | YOLOv8 (Ultralytics) |
| **API** | FastAPI, Uvicorn |
| **Containerization** | Docker, Docker Compose |
| **Testing** | pytest, dbt tests |
| **CI/CD** | GitHub Actions |
| **Code Quality** | Black, Flake8, mypy |
| **Documentation** | MkDocs, dbt docs |

## 🏗️ Architecture

### Data Flow
┌─────────────────────────────────────────────────────────────────────────────┐
│ DATA PIPELINE │
├─────────────────────────────────────────────────────────────────────────────┤
│ │
│ 📡 EXTRACT 🔄 LOAD 🔄 TRANSFORM │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Telegram │ ──────────▶ │ Data Lake │ ─────────▶ │ PostgreSQL │ │
│ │ Channels │ │ (JSON) │ │ (Warehouse)│ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ │ │ │ │
│ ▼ ▼ ▼ │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ Images │ │ dbt │ │ Star │ │
│ │ Download │ │ Staging │ │ Schema │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ │
│ 🔍 ENRICHMENT 📊 ANALYTICS 🚀 DELIVERY │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ YOLOv8 │ ──────────▶ │ FastAPI │ ─────────▶ │ Reports │ │
│ │ Detection │ │ Endpoints │ │ Dashboard │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
│ │
│ ⚙️ ORCHESTRATION │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Dagster │ │
│ │ ├── scrape_telegram_data │ │
│ │ ├── load_raw_to_postgres │ │
│ │ ├── run_dbt_transformations │ │
│ │ └── run_yolo_enrichment │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────────────────────────┘

text

## 📊 Data Model

### Star Schema
┌─────────────────────┐ ┌─────────────────────┐
│ dim_channels │ │ dim_dates │
│ │ │ │
│ channel_key (PK) │ │ date_key (PK) │
│ channel_name │────────▶│ date_full │
│ channel_type │ │ day_of_week │
│ first_post_date │ │ month │
│ last_post_date │ │ quarter │
│ total_posts │ │ year │
│ avg_views │ │ is_weekend │
└─────────────────────┘ └─────────────────────┘
│ │
│ │
▼ ▼
┌─────────────────────────────────────────────────────┐
│ fct_messages │
│ │
│ message_key (PK) │
│ message_id │
│ channel_key (FK) ──────────────────────────────────▶│
│ date_key (FK) ──────────────────────────────────────▶│
│ message_text │
│ message_length │
│ view_count │
│ forward_count │
│ has_image_flag │
└─────────────────────────────────────────────────────┘

text

### Tables

#### Dimension Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| **dim_channels** | Channel metadata and aggregates | channel_key, channel_name, channel_type, total_posts, avg_views |
| **dim_dates** | Date dimension for time analysis | date_key, date_full, day_of_week, month, year, is_weekend |

#### Fact Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| **fct_messages** | Message facts and metrics | message_key, message_id, channel_key(FK), date_key(FK), views, forwards |
| **fct_image_detections** | Image detection results | message_id, detected_class, confidence_score, image_category |

## 🚀 Getting Started

### Prerequisites


# Required
Python 3.10+
Docker & Docker Compose (optional)
PostgreSQL 15 (or SQLite for development)
Git

# Telegram API Credentials
Get from: https://my.telegram.org
Installation
bash
# 1. Clone the repository
git clone https://github.com/arsema16/medical-telegram-warehouse.git
cd medical-telegram-warehouse

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 5. Start PostgreSQL (optional)
docker-compose up -d postgres

# 6. Run the complete pipeline
python scripts/run_complete_pipeline.py
Quick Start with Mock Data
bash
# 1. Create mock data
python scripts/create_mock_data.py

# 2. Load data to SQLite
python scripts/load_data_simple.py

# 3. Start the API
uvicorn api.main:app --reload

# 4. View API documentation
open http://localhost:8000/docs
📁 Project Structure
text
```medical-telegram-warehouse/
├── .github/
│   └── workflows/
│       └── unittests.yml          # CI/CD pipeline
├── api/                           # FastAPI application
│   ├── __init__.py
│   ├── main.py                    # API endpoints
│   ├── database.py                # Database connection
│   └── schemas.py                 # Pydantic models
├── data/                          # Data storage
│   ├── raw/                       # Data lake
│   │   ├── telegram_messages/     # JSON data by date
│   │   └── images/                # Downloaded images
│   └── warehouse.db               # SQLite database
├── medical_warehouse/             # dbt project
│   ├── models/
│   │   ├── staging/               # Staging models
│   │   │   └── stg_telegram_messages.sql
│   │   └── marts/                 # Mart models
│   │       ├── dim_channels.sql
│   │       ├── dim_dates.sql
│   │       └── fct_messages.sql
│   ├── tests/                     # dbt tests
│   │   ├── assert_no_future_messages.sql
│   │   └── assert_positive_views.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── scripts/                       # Utility scripts
│   ├── create_mock_data.py        # Mock data generator
│   ├── load_data_simple.py        # SQLite loader
│   ├── run_scraper.py             # Telegram scraper
│   ├── run_loader.py              # PostgreSQL loader
│   ├── run_tests.py               # Test runner
│   └── run_complete_pipeline.py   # Complete pipeline
├── src/                           # Source code
│   ├── scraper.py                 # Telegram scraper
│   ├── data_loader.py             # PostgreSQL loader
│   └── yolo_detect.py             # YOLO detection
├── tests/                         # Unit tests
│   ├── test_scraper.py
│   ├── test_data_loader.py
│   └── test_dbt_models.py
├── notebooks/                     # Jupyter notebooks
├── logs/                          # Application logs
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Python environment
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration
├── pytest.ini                     # Test configuration
└── README.md                      # This file
```
🌐 API Documentation
Endpoints
Method	Endpoint	Description	Example
GET	/	Welcome message	-
GET	/api/messages/stats	Overall statistics	-
GET	/api/reports/top-products	Top mentioned products	?limit=10&channel=chemed
GET	/api/channels/{channel_name}/activity	Channel activity	/api/channels/chemed/activity?days=7
GET	/api/search/messages	Search messages	?query=paracetamol&limit=20
GET	/api/reports/visual-content	Visual content statistics	-
GET	/api/reports/daily-trends	Daily trends	?days=7
Example Response
json
{
  "products": [
    {
      "product": "Vitamin",
      "mentions": 27,
      "avg_views": 312.5,
      "avg_forwards": 15.2
    },
    {
      "product": "Ibuprofen",
      "mentions": 18,
      "avg_views": 287.3,
      "avg_forwards": 12.8
    }
  ],
  "total_products_mentioned": 12,
  "channel_filter": "All channels",
  "limit": 10
}
API Documentation
Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

🧪 Testing
bash
# Run all tests
python scripts/run_tests.py

# Run unit tests only
pytest tests/ -v -m "not integration" --cov=src

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=html

# Run dbt tests
cd medical_warehouse && dbt test
🐳 Docker Support
bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Start only PostgreSQL
docker-compose up -d postgres
📈 Performance Metrics
Operation	Time	Messages
Scraping (500 messages/channel)	~2-3 min	1,500
Data Loading	~10-20 sec	654
dbt Run	~30-60 sec	-
API Response	<100ms	-
🤝 Contributing
Fork the repository

Create a feature branch

bash
git checkout -b feature/amazing-feature
Commit your changes

bash
git commit -m 'Add amazing feature'
Push to the branch

bash
git push origin feature/amazing-feature
Open a Pull Request

Development Guidelines
✅ Write tests for new features

✅ Update documentation

✅ Follow PEP 8 style guide

✅ Run black and flake8 before committing

📄 License
This project is part of the 10 Academy Artificial Intelligence Mastery program.



Telegram for the API

Ultralytics for YOLOv8

dbt Labs for dbt

Dagster for orchestration

📞 Support
Slack: #all-week8

Issues: GitHub Issues

Documentation: Wiki

🚀 Quick Commands
bash
# Scrape real Telegram data
python scripts/run_scraper.py

# Load data to database
python scripts/load_data_simple.py

# Start API
uvicorn api.main:app --reload

# Run dbt
cd medical_warehouse && dbt run && cd ..

# Run all tests
python scripts/run_tests.py
<div align="center"> <sub>Built with ❤️ by <a href="https://github.com/arsema16">Arsema</a></sub> </div> ```
