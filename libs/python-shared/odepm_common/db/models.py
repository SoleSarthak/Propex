from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Boolean,
    Text,
    Numeric,
    Computed,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from .session import Base


class Cve(Base):
    __tablename__ = "cves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(25), unique=True, nullable=False)
    source = Column(String(10), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    last_modified_at = Column(DateTime(timezone=True))
    cvss_score = Column(Numeric(3, 1))
    cvss_version = Column(String(5))
    cvss_vector = Column(Text)
    severity_tier = Column(
        String(10),
        Computed(
            "CASE "
            "WHEN cvss_score >= 9.0 THEN 'Critical' "
            "WHEN cvss_score >= 7.0 THEN 'High' "
            "WHEN cvss_score >= 4.0 THEN 'Medium' "
            "ELSE 'Low' END"
        ),
    )
    description = Column(Text)
    raw_data = Column(JSONB)
    resolution_status = Column(String(20), default="pending")
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    affected_packages = relationship(
        "CveAffectedPackage", back_populates="cve", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "source IN ('nvd', 'osv', 'ghsa', 'manual')", name="check_source"
        ),
        CheckConstraint(
            "resolution_status IN ('pending', 'resolving', 'resolved', 'failed')",
            name="check_resolution_status",
        ),
    )


class CveAffectedPackage(Base):
    __tablename__ = "cve_affected_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(
        UUID(as_uuid=True), ForeignKey("cves.id", ondelete="CASCADE"), nullable=False
    )
    ecosystem = Column(String(10), nullable=False)
    package_name = Column(String(300), nullable=False)
    versions_affected = Column(ARRAY(Text), nullable=False)
    fixed_version = Column(String(100))
    purl = Column(Text)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    cve = relationship("Cve", back_populates="affected_packages")
    affected_repositories = relationship(
        "AffectedRepository",
        back_populates="cve_affected_package",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "ecosystem IN ('npm', 'pypi', 'maven')", name="check_ecosystem"
        ),
    )


class Package(Base):
    __tablename__ = "packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ecosystem = Column(String(10), nullable=False)
    name = Column(String(300), nullable=False)
    latest_version = Column(String(100))
    weekly_downloads = Column(Integer, default=0)
    total_dependents = Column(Integer, default=0)
    homepage_url = Column(Text)
    repository_url = Column(Text)
    description = Column(Text)
    metadata_fetched_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "ecosystem IN ('npm', 'pypi', 'maven')", name="check_ecosystem"
        ),
    )


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, unique=True, nullable=False)
    owner = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    full_name = Column(String(400), Computed("owner || '/' || name"))
    default_branch = Column(String(100), default="main")
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    language = Column(String(50))
    is_archived = Column(Boolean, default=False)
    is_fork = Column(Boolean, default=False)
    weekly_downloads = Column(Integer, default=0)
    metadata_fetched_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AffectedRepository(Base):
    __tablename__ = "affected_repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_affected_package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cve_affected_packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    repo_url = Column(Text, nullable=False)
    repo_owner = Column(Text, nullable=False)
    repo_name = Column(Text, nullable=False)

    dependency_depth = Column(Integer, nullable=False, default=1)
    dependency_path = Column(ARRAY(Text), nullable=False)
    dependency_file = Column(Text)
    version_spec = Column(String)
    context_type = Column(String(20))

    cvss_base = Column(Numeric(3, 1))
    depth_factor = Column(Numeric(4, 3))
    context_multiplier = Column(Numeric(4, 3))
    popularity_factor = Column(Numeric(4, 3))
    context_score = Column(Numeric(4, 2))
    severity_tier = Column(String(10))

    notification_status = Column(String(20), default="pending")
    issue_url = Column(Text)
    notified_at = Column(DateTime(timezone=True))

    maintainer_status = Column(String(20))
    maintainer_updated_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    cve_affected_package = relationship(
        "CveAffectedPackage", back_populates="affected_repositories"
    )

    __table_args__ = (
        CheckConstraint(
            "context_type IN ('runtime', 'dev', 'peer', 'test', 'optional', 'unknown')",
            name="check_context_type",
        ),
        CheckConstraint(
            "severity_tier IN ('Critical', 'High', 'Medium', 'Low')",
            name="check_severity_tier",
        ),
        CheckConstraint(
            "notification_status IN ('pending', 'queued', 'sent', 'skipped_opt_out', 'skipped_duplicate', 'failed')",
            name="check_notification_status",
        ),
        CheckConstraint(
            "maintainer_status IN ('patched', 'not_affected', 'wont_fix')",
            name="check_maintainer_status",
        ),
    )
