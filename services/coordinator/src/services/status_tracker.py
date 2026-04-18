import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from odepm_common.db.models import Cve
from datetime import datetime

logger = logging.getLogger(__name__)

class StatusTracker:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_status(self, cve_id: str, status: str):
        """
        Update the resolution status of a CVE in PostgreSQL.
        """
        try:
            result = await self.session.execute(
                select(Cve).where(Cve.cve_id == cve_id)
            )
            cve = result.scalars().first()
            if cve:
                cve.resolution_status = status
                if status == "resolved":
                    cve.resolved_at = datetime.utcnow()
                
                cve.updated_at = datetime.utcnow()
                await self.session.commit()
                logger.info(f"Updated status for {cve_id} to {status}")
            else:
                logger.warning(f"CVE {cve_id} not found in database to update status.")
        except Exception as e:
            logger.error(f"Failed to update status for {cve_id}: {e}")
            await self.session.rollback()
            raise
