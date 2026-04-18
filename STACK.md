# 🛠️ Technology Stack - Propex

Propex uses a modern, high-performance "Free Tier Optimized" stack designed for massive graph traversal and real-time security analytics.

## 🎨 Frontend (Web Dashboard)
- **Framework**: [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Language**: TypeScript
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/) (Modern, performance-first)
- **Icons**: [Lucide React](https://lucide.dev/)
- **State Management**: [Zustand](https://github.com/pmndrs/zustand)
- **Data Fetching**: [TanStack Query v5](https://tanstack.com/query/latest)
- **Routing**: [React Router v7](https://reactrouter.com/)
- **Animations**: [Tailwind Animate](https://github.com/jamiebuilds/tailwindcss-animate)

## ⚙️ Backend (Microservices)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (High performance, async-first)
- **Language**: Python 3.12+
- **Task Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/)
- **Async HTTP Client**: [HTTPX](https://www.python-httpx.org/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)

## 🗄️ Databases & Storage
- **Relational**: [PostgreSQL 16](https://www.postgresql.org/) (CVE metadata, application state)
- **Graph**: [Neo4j Community 5](https://neo4j.com/) (Dependency propagation graph)
- **Cache**: [Redis 7](https://redis.io/) (Resolver results, session data)
- **Object Storage**: [MinIO](https://min.io/) (S3-compatible archival of raw API responses)

## 📨 Event Streaming
- **Message Broker**: [Redpanda](https://redpanda.com/) (Kafka-compatible, low latency, no JVM)
- **Management**: Redpanda Console (Web UI for topic inspection)

## 📈 Observability & DevOps
- **Metrics**: [Prometheus](https://prometheus.io/)
- **Dashboards**: [Grafana](https://grafana.com/)
- **Tracing**: [Jaeger](https://www.jaegertracing.io/) (OpenTelemetry compatible)
- **Orchestration**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (Currently disabled per user request)

## 🛠️ Tooling
- **Dependency Management**: Poetry (Python), npm (Node)
- **Task Runner**: Make
- **Linting/Formatting**: Black, Flake8, Mypy, ESLint

---

## 🔄 Data Architecture & Flow

### 1. Ingestion Layer
- **CVE Ingestion Service**: Polls NVD/GHSA/OSV APIs every 15 mins.
- **Normalizer**: Converts raw vendor JSON into standard `CveRecord`.
- **Archiver**: Saves raw responses to **MinIO** for audit/replay.

### 2. Coordination & Routing
- **Redpanda (Kafka)**: Acts as the high-speed nervous system (`cve.raw` topic).
- **Coordinator**: Consumes raw CVEs and routes them to ecosystem-specific resolvers (npm, PyPI, Maven).

### 3. Resolution & Graph Analysis
- **npm Resolver**: Performs BFS traversal of the dependency tree.
- **Libraries.io / GitHub**: Used for reverse dependency discovery.
- **Neo4j**: Stores the "Blast Radius" as a graph of Packages and Repositories.

### 4. Risk Assessment
- **Scoring Engine**: Calculates a 0-10 risk score for every affected project based on depth, context, and popularity.

### 5. Presentation
- **Web Dashboard**: Real-time React app showing security trends and the propagation graph.
- **Monitoring**: Grafana dashboards tracking ingestion lag and system health.
