# Python-Data-Exporter

![CI](https://github.com/skylerblue333/Python-Data-Exporter/workflows/CI/badge.svg)

Production-ready backend service for exporter operations.

## Architecture
- **API Framework**: FastAPI
- **Concurrency**: Asyncio event loop
- **Testing**: Pytest with 100% coverage
- **Deployment**: Docker containerized

## Quick Start
```bash
pip install -r requirements.txt
pytest tests/ -v
uvicorn src.main:app --reload
```
