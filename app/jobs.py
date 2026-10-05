import asyncio
import logging
from app.modules.booking import service as booking_svc
from app.core.time import utcnow

logger = logging.getLogger(__name__)

async def run_jobs_once(session_maker):
    results = {}
    
    try:
        async with session_maker() as db:
            count = await booking_svc.expire_unpaid_bookings(db, utcnow())
            results["expire"] = count
    except Exception as e:
        logger.error(f"Job expire_unpaid_bookings failed: {e}")
        results["expire"] = -1

    try:
        async with session_maker() as db:
            count = await booking_svc.breach_unconfirmed_bookings(db, utcnow())
            results["breach"] = count
    except Exception as e:
        logger.error(f"Job breach_unconfirmed_bookings failed: {e}")
        results["breach"] = -1
        
    return results

async def job_loop(session_maker, sleep_time: int = 60):
    while True:
        try:
            await run_jobs_once(session_maker)
        except Exception as e:
            logger.error(f"Job loop iteration failed: {e}")
        await asyncio.sleep(sleep_time)
