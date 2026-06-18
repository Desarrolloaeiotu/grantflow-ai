"""
API endpoints para ejecutar scrapers manualmente
"""
import asyncio
import structlog
from fastapi import APIRouter, BackgroundTasks

from app.scrapers.utils.contacts_scraper import scrape_all_contacts
# from app.scrapers.tenders_global_scraper import run_global_scraping  # TODO: Fix imports

logger = structlog.get_logger()
router = APIRouter()


@router.post("/scrape/contacts")
async def scrape_contacts_endpoint(background_tasks: BackgroundTasks) -> dict:
    """Ejecutar scraper de contactos en background"""
    background_tasks.add_task(scrape_all_contacts)
    logger.info("Started contacts scraping task")
    return {
        "status": "started",
        "message": "Contacts scraping initiated in background",
    }


# @router.post("/scrape/tenders-global")
# async def scrape_tenders_global_endpoint(background_tasks: BackgroundTasks) -> dict:
#     """Ejecutar scraper de tenders global en background"""
#     background_tasks.add_task(run_global_scraping)
#     logger.info("Started global tenders scraping task")
    return {
        "status": "started",
        "message": "Global tenders scraping initiated in background",
    }


@router.post("/scrape/all")
async def scrape_all_endpoint(background_tasks: BackgroundTasks) -> dict:
    """Ejecutar todos los scrapers"""
    background_tasks.add_task(scrape_all_contacts)
    background_tasks.add_task(run_global_scraping)
    logger.info("Started all scraping tasks")
    return {
        "status": "started",
        "message": "All scraping tasks initiated in background",
    }
