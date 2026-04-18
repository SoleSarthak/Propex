import asyncio
import os
import sys
from datetime import datetime

# Add libs to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "libs", "python-shared"))

from odepm_common.models.cve import CveRecord, AffectedPackage  # noqa: E402
from odepm_common.db.session import get_async_sessionmaker  # noqa: E402


async def seed_db():
    print("Seeding database...")

    cves = [
        CveRecord(
            cve_id="CVE-2021-44228",
            source="NVD",
            published_at=datetime(2021, 12, 10),
            cvss_score=10.0,
            affected_packages=[
                AffectedPackage(
                    ecosystem="maven",
                    name="org.apache.logging.log4j:log4j-core",
                    versions_affected=["2.0-beta9", "2.14.1"],
                    fixed_version="2.15.0",
                )
            ],
            description="Apache Log4j2 JNDI features do not protect against attacker controlled LDAP and other JNDI related endpoints.",
        ),
        CveRecord(
            cve_id="CVE-2024-21626",
            source="NVD",
            published_at=datetime(2024, 1, 31),
            cvss_score=8.6,
            affected_packages=[
                AffectedPackage(
                    ecosystem="pypi",
                    name="runc",
                    versions_affected=["<1.1.12"],
                    fixed_version="1.1.12",
                )
            ],
            description="runc is a CLI tool for spawning and running containers according to the OCI specification. In runc 1.1.11 and earlier, several file descriptor leaks...",
        ),
        CveRecord(
            cve_id="CVE-2023-45853",
            source="NVD",
            published_at=datetime(2023, 10, 13),
            cvss_score=9.8,
            affected_packages=[
                AffectedPackage(
                    ecosystem="npm",
                    name="zlib",
                    versions_affected=["<1.3"],
                    fixed_version="1.3",
                )
            ],
            description="MiniZip in zlib through 1.3 has a heap-based buffer over-read in zipOpenNewFileInZip4_64.",
        ),
        CveRecord(
            cve_id="CVE-2024-1234",
            source="Internal",
            published_at=datetime.now(),
            cvss_score=7.5,
            affected_packages=[
                AffectedPackage(
                    ecosystem="npm",
                    name="express",
                    versions_affected=["<4.18.2"],
                    fixed_version="4.18.2",
                )
            ],
            description="Sample internal vulnerability for testing purposes.",
        ),
    ]

    async with get_async_sessionmaker()():
        # This is a stub since we haven't defined the SQLAlchemy models for CVEs yet
        # But we can at least log what we would do
        print(f"Would insert {len(cves)} CVE records into the database.")
        # session.add_all(...)
        # await session.commit()

    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_db())
