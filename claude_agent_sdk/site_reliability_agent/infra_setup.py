#!/usr/bin/env python3
"""
Infrastructure setup for the SRE Incident Response Agent notebook.

Generates local Docker-based infrastructure:
- config/            Docker Compose, Prometheus, database init, API server env
- services/          FastAPI API server, Dockerfile, and dependencies
- scripts/           Traffic generator and healthy-services simulator
- hooks/             Safety hook scripts for validating agent write operations
- postmortems/       Directory for agent-generated post-mortems

Usage:
    python infra_setup.py
"""

import os
import stat
from pathlib import Path

for d in ["config", "services", "scripts", "hooks", "postmortems"]:
    os.makedirs(d, exist_ok=True)

# =============================================================================
# DOCKER COMPOSE
# =============================================================================
# Defines the full service stack:
#   - postgres:           PostgreSQL 15 database with health checks
#   - api-server:         FastAPI app that queries the DB and exposes Prometheus metrics
#   - healthy-services:   Simulates healthy payment-svc
#                         and auth-svc (for baseline metrics)
#   - traffic-generator:  Sends ~50 req/s to the API server to generate continuous load
#   - prometheus:         Scrapes metrics from api-server every 5 seconds
#   - grafana:            Optional dashboard UI (accessible at localhost:3000)

Path("config/docker-compose.yml").write_text("""\
services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:  # Demo only — change for any non-local deployment
      POSTGRES_USER: demo
      POSTGRES_PASSWORD: demo
      POSTGRES_DB: demo
    ports:
      - "5432:5432"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U demo -d demo"]
      interval: 5s
      timeout: 5s
      retries: 5

  # API Server
  api-server:
    build:
      context: ../services
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file:
      - ./api-server.env
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Healthy Services Metrics (payment-svc, auth-svc simulation)
  healthy-services:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ../scripts/healthy_services.py:/app/healthy_services.py
    command: python healthy_services.py
    ports:
      - "8001:8001"
    restart: unless-stopped

  # Traffic Generator
  traffic-generator:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ../scripts/traffic_generator.py:/app/traffic_generator.py
    command: >
      sh -c "pip install aiohttp && python traffic_generator.py"
    environment:
      - API_HOST=api-server
      - API_PORT=8080
      - REQUESTS_PER_SECOND=50
    depends_on:
      api-server:
        condition: service_healthy
    restart: unless-stopped

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    extra_hosts:
      # Allows Prometheus to scrape the API server running on the host.
      # Requires Docker Desktop (macOS/Windows) or --add-host on Linux.
      - "host.docker.internal:host-gateway"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    depends_on:
      - api-server

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      # Demo only — change for any non-local deployment
      - GF_SECURITY_ADMIN_PASSWORD=demo
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    volumes:
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    depends_on:
      - prometheus

volumes:
  postgres_data:
""")

# =============================================================================
# API SERVER CONFIGURATION
# =============================================================================
# Environment variables for the api-server container.
# DB_POOL_SIZE is the key parameter we'll manipulate during the incident:
#   - Healthy value: 20 (handles concurrent requests comfortably)
#   - Broken value:  1  (causes connection pool exhaustion under load)

Path("config/api-server.env").write_text("""\
# API Server Configuration
# This file is read by the api-server container

# Database connection pool settings
# docker-compose -f config/docker-compose.yml up --build api-server
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=2

# Database connection — demo only, change for any non-local deployment
DB_HOST=postgres
DB_PORT=5432
DB_NAME=demo
DB_USER=demo
DB_PASSWORD=demo

# Service identification
SERVICE_NAME=api-server
""")

# Known-good backup of the config (the agent can reference this during investigation)
Path("config/api-server.env.backup").write_text("""\
# API Server Configuration - KNOWN GOOD VALUES
# Use this as a reference for the correct configuration

# Database connection pool settings
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=2

# Database connection — demo only, change for any non-local deployment
DB_HOST=postgres
DB_PORT=5432
DB_NAME=demo
DB_USER=demo
DB_PASSWORD=demo

# Service identification
SERVICE_NAME=api-server
""")

# =============================================================================
# PROMETHEUS CONFIGURATION
# =============================================================================
# Scrapes the api-server's /metrics endpoint every 5 seconds.
# The agent queries Prometheus via its HTTP API (localhost:9090) to check
# error rates, latency percentiles, and DB connection pool utilization.

Path("config/prometheus.yml").write_text("""\
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'api-server'
    static_configs:
      - targets: ['api-server:8080']
    metrics_path: /metrics
""")

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
# Creates the schema used by the API server. PostgreSQL runs this automatically
# on first startup via the docker-entrypoint-initdb.d volume mount.

Path("config/init.sql").write_text("""\
-- Database initialization script for SRE Demo
-- Creates tables and sample data

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (name, email) VALUES
    ('Alice Johnson', 'alice@example.com'),
    ('Bob Smith', 'bob@example.com'),
    ('Carol Williams', 'carol@example.com'),
    ('David Brown', 'david@example.com'),
    ('Eva Martinez', 'eva@example.com'),
    ('Frank Garcia', 'frank@example.com'),
    ('Grace Lee', 'grace@example.com'),
    ('Henry Wilson', 'henry@example.com'),
    ('Ivy Chen', 'ivy@example.com'),
    ('Jack Taylor', 'jack@example.com')
ON CONFLICT (email) DO NOTHING;

-- Insert sample orders
INSERT INTO orders (user_id, total, status) VALUES
    (1, 99.99, 'completed'),
    (1, 149.50, 'completed'),
    (2, 75.00, 'pending'),
    (3, 200.00, 'completed'),
    (4, 45.99, 'shipped'),
    (5, 320.00, 'completed'),
    (6, 89.99, 'pending'),
    (7, 175.50, 'completed'),
    (8, 55.00, 'cancelled'),
    (9, 450.00, 'completed'),
    (10, 125.00, 'shipped'),
    (1, 67.50, 'completed'),
    (2, 230.00, 'completed'),
    (3, 95.00, 'pending'),
    (4, 180.00, 'completed');
""")

# Grafana datasource provisioning (points Grafana at the local Prometheus)
Path("config/grafana-datasources.yml").write_text("""\
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
""")

# =============================================================================
# API SERVER (FastAPI Application)
# =============================================================================
# This is the service we'll break and fix. Key characteristics:
#
#   - Connects to PostgreSQL with a configurable connection pool (DB_POOL_SIZE)
#   - Exposes Prometheus metrics at /metrics:
#       * http_requests_total (counter, by status code and endpoint)
#       * http_request_duration_milliseconds (histogram, p50/p90/p99)
#       * db_connections_active (gauge, current pool usage)
#       * db_pool_size (gauge, configured pool size)
#   - When DB_POOL_SIZE=1 under load, connections exhaust immediately,
#     causing 500 errors, high latency, and "connection pool exhausted" logs
#
# The agent will observe these symptoms via Prometheus and container logs,
# trace them back to the config, and fix the pool size.

Path("services/api_server.py").write_text('''\
"""
API Server for SRE Bot Demo

A FastAPI service that connects to PostgreSQL with a configurable connection pool.
When DB_POOL_SIZE is set too low, it causes connection pool exhaustion under load.
"""

import os
import time
import asyncio
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Configuration from environment
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "demo")
DB_USER = os.getenv("DB_USER", "demo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "demo")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "5"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "api-server")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_milliseconds',
    'HTTP request latency in milliseconds',
    ['service', 'method', 'endpoint'],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
)

DB_CONNECTIONS_ACTIVE = Gauge(
    'db_connections_active',
    'Number of active database connections',
    ['service']
)

DB_CONNECTIONS_MAX = Gauge(
    'db_connections_max',
    'Maximum database connections in pool',
    ['service']
)

DB_POOL_SIZE_GAUGE = Gauge(
    'db_pool_size',
    'Configured database pool size',
    ['service']
)

# Database setup
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = None
SessionLocal = None

# Thread pool for running sync database code concurrently
executor = ThreadPoolExecutor(max_workers=20)


def init_database():
    """Initialize database connection with configured pool size."""
    global engine, SessionLocal

    logger.info(
        f"Initializing database connection pool"
        f" with size={DB_POOL_SIZE},"
        f" timeout={DB_POOL_TIMEOUT}s"
    )

    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=0,  # No extra connections beyond pool_size
        pool_timeout=DB_POOL_TIMEOUT,  # Seconds to wait for a connection
        pool_pre_ping=True,  # Verify connections before using
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Update metrics
    DB_POOL_SIZE_GAUGE.labels(service=SERVICE_NAME).set(DB_POOL_SIZE)
    DB_CONNECTIONS_MAX.labels(service=SERVICE_NAME).set(DB_POOL_SIZE)

    logger.info(f"Database pool initialized: pool_size={DB_POOL_SIZE}, max_overflow=0")


def update_connection_metrics():
    """Update Prometheus metrics for database connections."""
    if engine:
        pool = engine.pool
        DB_CONNECTIONS_ACTIVE.labels(service=SERVICE_NAME).set(pool.checkedout())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {SERVICE_NAME}")
    logger.info(f"DB_POOL_SIZE={DB_POOL_SIZE}")

    # Wait for database to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            init_database()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            break
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Database not ready, retrying in 1s... ({e})")
                await asyncio.sleep(1)
            else:
                logger.error(
                    f"Could not connect to database"
                    f" after {max_retries} retries"
                )
                raise

    yield

    # Shutdown
    logger.info("Shutting down")
    if engine:
        engine.dispose()


app = FastAPI(title="SRE Demo API Server", lifespan=lifespan)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": SERVICE_NAME,
            "db_pool_size": DB_POOL_SIZE,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    update_connection_metrics()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _sync_list_users():
    """Synchronous database operation for list_users."""
    with SessionLocal() as session:
        # Simulate slow query to cause pool exhaustion when DB_POOL_SIZE is too low
        session.execute(text("SELECT pg_sleep(0.2)"))
        result = session.execute(text("SELECT id, name, email FROM users LIMIT 100"))
        return [{"id": row[0], "name": row[1], "email": row[2]} for row in result]


@app.get("/api/users")
async def list_users():
    """List all users from the database."""
    start_time = time.time()
    status = "200"

    try:
        # Occasional random error for realism (~1% error rate)
        if random.random() < 0.01:
            status = "500"
            raise HTTPException(status_code=500, detail="Transient database error")

        update_connection_metrics()

        # Run sync DB code in thread pool to allow concurrent requests
        loop = asyncio.get_running_loop()
        users = await loop.run_in_executor(executor, _sync_list_users)

        return {"users": users, "count": len(users)}

    except (OperationalError, SQLAlchemyTimeoutError) as e:
        status = "500"
        error_msg = str(e)

        if "QueuePool limit" in error_msg or "TimeoutError" in error_msg:
            logger.error(f"Connection pool exhausted: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=(
                    "Database connection pool"
                    " exhausted. QueuePool limit"
                    f" of size {DB_POOL_SIZE}"
                    " reached, connection"
                    " timed out."
                )
            )
        else:
            logger.error(f"Database error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")

    except Exception as e:
        status = "500"
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        duration_ms = (time.time() - start_time) * 1000
        REQUEST_COUNT.labels(
            service="user-svc", method="GET",
            endpoint="/api/users", status=status,
        ).inc()
        REQUEST_LATENCY.labels(
            service="user-svc", method="GET",
            endpoint="/api/users",
        ).observe(duration_ms)


@app.get("/api/orders")
async def list_orders():
    """List recent orders - returns cached data, mostly healthy."""
    start_time = time.time()
    status = "200"

    try:
        # Occasional random error for realism (~1% error rate)
        if random.random() < 0.01:
            status = "500"
            raise HTTPException(status_code=500, detail="Transient cache error")

        # Return mock/cached data - doesn't use database connection pool
        orders = [
            {
                "id": i, "user_id": i % 10 + 1,
                "total": round(random.uniform(10, 500), 2),
                "status": "completed",
                "user_name": f"User {i % 10 + 1}",
            }
            for i in range(1, 11)
        ]

        return {"orders": orders, "count": len(orders)}

    except HTTPException:
        raise

    except Exception as e:
        status = "500"
        logger.error(f"Orders endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        duration_ms = (time.time() - start_time) * 1000
        REQUEST_COUNT.labels(
            service="payment-svc", method="GET",
            endpoint="/api/orders", status=status,
        ).inc()
        REQUEST_LATENCY.labels(
            service="payment-svc", method="GET",
            endpoint="/api/orders",
        ).observe(duration_ms)


@app.get("/api/stats")
async def get_stats():
    """Get statistics - returns cached data, mostly healthy."""
    start_time = time.time()
    status = "200"

    try:
        # Occasional random error for realism (~1% error rate)
        if random.random() < 0.01:
            status = "500"
            raise HTTPException(status_code=500, detail="Transient cache error")

        # Return mock/cached data - doesn't use database connection pool
        return {
            "users_count": 1000 + random.randint(0, 50),
            "orders_count": 5000 + random.randint(0, 100),
            "total_revenue": round(random.uniform(50000, 55000), 2),
            "db_pool": {
                "size": DB_POOL_SIZE,
                "checked_out": 0,
                "overflow": 0,
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        status = "500"
        logger.error(f"Stats endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        duration_ms = (time.time() - start_time) * 1000
        REQUEST_COUNT.labels(
            service="auth-svc", method="GET",
            endpoint="/api/stats", status=status,
        ).inc()
        REQUEST_LATENCY.labels(
            service="auth-svc", method="GET",
            endpoint="/api/stats",
        ).observe(duration_ms)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": SERVICE_NAME,
        "endpoints": ["/health", "/metrics", "/api/users", "/api/orders", "/api/stats"],
        "config": {
            "db_pool_size": DB_POOL_SIZE,
            "db_pool_timeout": DB_POOL_TIMEOUT,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
''')

# =============================================================================
# DOCKERFILE & DEPENDENCIES
# =============================================================================
# Builds the api-server container. Uses a single Uvicorn worker to make
# pool exhaustion more pronounced (multiple workers would mask the issue).

Path("services/Dockerfile").write_text("""\
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_server.py .

# Expose port
EXPOSE 8080

# Run the application - single worker to demonstrate pool exhaustion
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
""")

# Python dependencies for the API server
Path("services/requirements.txt").write_text("""\
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
prometheus-client==0.19.0
""")

# =============================================================================
# HEALTHY SERVICES SIMULATOR
# =============================================================================
# Exposes fake Prometheus metrics for payment-svc and auth-svc.
# These always report healthy values, providing a contrast when the
# api-server starts failing during the incident.

Path("scripts/healthy_services.py").write_text('''\
#!/usr/bin/env python3
"""
Healthy Services Metrics Server

Exposes Prometheus-format metrics for simulated
healthy services (payment-svc, auth-svc).
These provide visual contrast against the real
api-server which can have actual incidents.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import random
import time

# Counters that accumulate over time
request_counts = {
    "payment-svc": {"200": 0, "500": 0},
    "auth-svc": {"200": 0, "500": 0},
}

last_update = time.time()


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        global last_update

        # Update counters based on time elapsed (roughly proportional to traffic rate)
        elapsed = time.time() - last_update
        if elapsed > 0.5:  # Update every 0.5 seconds
            # Always healthy traffic
            request_counts["payment-svc"]["200"] += int(elapsed * random.randint(8, 12))
            request_counts["payment-svc"]["500"] += (
                random.randint(0, 1)
                if random.random() > 0.9 else 0
            )
            request_counts["auth-svc"]["200"] += int(elapsed * random.randint(15, 20))
            request_counts["auth-svc"]["500"] += (
                random.randint(0, 1)
                if random.random() > 0.95 else 0
            )
            last_update = time.time()

        # Healthy latency values
        payment_latency_p99 = 100 + random.randint(0, 20)
        payment_latency_p50 = 45 + random.randint(0, 15)
        auth_latency_p99 = 85 + random.randint(0, 15)
        auth_latency_p50 = 25 + random.randint(0, 10)

        metrics = f"""# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total\
{{service="payment-svc",status="200"}} \
{request_counts["payment-svc"]["200"]}
http_requests_total\
{{service="payment-svc",status="500"}} \
{request_counts["payment-svc"]["500"]}
http_requests_total\
{{service="auth-svc",status="200"}} \
{request_counts["auth-svc"]["200"]}
http_requests_total\
{{service="auth-svc",status="500"}} \
{request_counts["auth-svc"]["500"]}

# HELP http_request_duration_milliseconds HTTP request latency
# TYPE http_request_duration_milliseconds_bucket gauge
http_request_duration_milliseconds_bucket\
{{service="payment-svc",le="100"}} {int(elapsed * 8)}
http_request_duration_milliseconds_bucket\
{{service="payment-svc",le="250"}} {int(elapsed * 10)}
http_request_duration_milliseconds_bucket\
{{service="payment-svc",le="+Inf"}} {int(elapsed * 10)}
http_request_duration_milliseconds_bucket\
{{service="auth-svc",le="100"}} {int(elapsed * 17)}
http_request_duration_milliseconds_bucket\
{{service="auth-svc",le="250"}} {int(elapsed * 18)}
http_request_duration_milliseconds_bucket\
{{service="auth-svc",le="+Inf"}} {int(elapsed * 18)}

# HELP container_cpu_usage_ratio CPU usage ratio by container
# TYPE container_cpu_usage_ratio gauge
container_cpu_usage_ratio\
{{container="payment-svc",namespace="production"}} \
{0.3 + random.uniform(0, 0.1):.3f}
container_cpu_usage_ratio\
{{container="auth-svc",namespace="production"}} \
{0.2 + random.uniform(0, 0.1):.3f}

# HELP container_memory_usage_ratio Memory usage ratio by container
# TYPE container_memory_usage_ratio gauge
container_memory_usage_ratio\
{{container="payment-svc",namespace="production"}} \
{0.4 + random.uniform(0, 0.1):.3f}
container_memory_usage_ratio\
{{container="auth-svc",namespace="production"}} \
{0.35 + random.uniform(0, 0.1):.3f}

# HELP up Service health status
# TYPE up gauge
up{{service="payment-svc"}} 1
up{{service="auth-svc"}} 1
"""

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(metrics.encode())

    def log_message(self, format, *args):
        pass  # Suppress logs


def main():
    port = 8001
    server = HTTPServer(("", port), MetricsHandler)
    print(f"Healthy services metrics: http://localhost:{port}/metrics")
    server.serve_forever()


if __name__ == "__main__":
    main()
''')

# =============================================================================
# TRAFFIC GENERATOR
# =============================================================================
# Sends continuous HTTP requests to the API server (~50 req/s).
# This ensures Prometheus always has fresh metrics to scrape.
# When the DB pool is exhausted, the traffic generator's requests start
# failing, which shows up as elevated error rates in Prometheus.

Path("scripts/traffic_generator.py").write_text('''\
#!/usr/bin/env python3
"""
Traffic Generator for SRE Demo

Sends continuous HTTP requests to the API server to create baseline load.
This is necessary to trigger connection pool exhaustion when DB_POOL_SIZE is too low.
"""

import asyncio
import aiohttp
import random
import logging
import os
import signal
import sys
from datetime import datetime

# Configuration
API_HOST = os.getenv("API_HOST", "api-server")
API_PORT = os.getenv("API_PORT", "8080")
REQUESTS_PER_SECOND = int(os.getenv("REQUESTS_PER_SECOND", "20"))

BASE_URL = f"http://{API_HOST}:{API_PORT}"
ENDPOINTS = ["/api/users", "/api/orders", "/api/stats"]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Statistics
stats = {
    "total_requests": 0,
    "successful": 0,
    "failed": 0,
    "start_time": None
}

running = True


def signal_handler(sig, frame):
    global running
    logger.info("Shutting down traffic generator...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def make_request(session: aiohttp.ClientSession, endpoint: str):
    """Make a single HTTP request to the API server."""
    url = f"{BASE_URL}{endpoint}"
    stats["total_requests"] += 1

    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status == 200:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
                if stats["failed"] % 10 == 1:  # Log every 10th failure
                    logger.warning(f"Request failed: {endpoint} -> {response.status}")
    except asyncio.TimeoutError:
        stats["failed"] += 1
        logger.warning(f"Request timeout: {endpoint}")
    except aiohttp.ClientError as e:
        stats["failed"] += 1
        if stats["failed"] % 10 == 1:
            logger.warning(f"Request error: {endpoint} -> {e}")
    except Exception as e:
        stats["failed"] += 1
        logger.error(f"Unexpected error: {endpoint} -> {e}")


async def print_stats():
    """Print statistics periodically."""
    while running:
        await asyncio.sleep(10)
        if stats["start_time"]:
            elapsed = (datetime.now() - stats["start_time"]).total_seconds()
            rps = stats["total_requests"] / elapsed if elapsed > 0 else 0
            success_rate = (
                (stats["successful"]
                 / stats["total_requests"] * 100)
                if stats["total_requests"] > 0
                else 0
            )

            logger.info(
                f"Stats: {stats['total_requests']} total, "
                f"{stats['successful']} success, {stats['failed']} failed, "
                f"{rps:.1f} req/s, {success_rate:.1f}% success rate"
            )


async def wait_for_api():
    """Wait for the API server to be ready."""
    logger.info(f"Waiting for API server at {BASE_URL}...")

    async with aiohttp.ClientSession() as session:
        for i in range(60):  # Wait up to 60 seconds
            try:
                async with session.get(
                    f"{BASE_URL}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        logger.info("API server is ready!")
                        return True
            except Exception:
                pass

            await asyncio.sleep(1)
            if i % 5 == 0:
                logger.info(f"Still waiting for API server... ({i}s)")

    logger.error("API server did not become ready in time")
    return False


async def generate_traffic():
    """Main traffic generation loop."""
    global running

    if not await wait_for_api():
        return

    stats["start_time"] = datetime.now()
    delay = 1.0 / REQUESTS_PER_SECOND

    logger.info(f"Starting traffic generation: {REQUESTS_PER_SECOND} requests/second")

    # Start stats printer
    stats_task = asyncio.create_task(print_stats())

    async with aiohttp.ClientSession() as session:
        while running:
            endpoint = random.choice(ENDPOINTS)
            asyncio.create_task(make_request(session, endpoint))
            await asyncio.sleep(delay)

    stats_task.cancel()

    # Final stats
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    logger.info(f"Final stats: {stats['total_requests']} requests in {elapsed:.1f}s")
    logger.info(f"Success: {stats['successful']}, Failed: {stats['failed']}")


if __name__ == "__main__":
    logger.info("Traffic Generator starting...")
    logger.info(f"Target: {BASE_URL}")
    logger.info(f"Rate: {REQUESTS_PER_SECOND} requests/second")

    try:
        asyncio.run(generate_traffic())
    except KeyboardInterrupt:
        logger.info("Traffic generator stopped")
''')

# =============================================================================
# SAFETY HOOKS
# =============================================================================
# Shell scripts that validate agent write operations before they execute.
# The Claude Agent SDK runs these as PreToolUse hooks — if a hook exits
# with a non-zero status, the tool call is blocked.
#
#   validate_pool_size.sh:
#     Ensures DB_POOL_SIZE changes stay within 5–100 (safe operating range).
#     Triggered before edit_config_file calls.
#
#   validate_config_before_deploy.sh:
#     Checks that config values are sane before allowing a deploy command.
#     Triggered before run_shell_command calls that redeploy the api-server.

Path("hooks/validate_pool_size.sh").write_text("""\
#!/bin/bash
# Validates that DB_POOL_SIZE changes stay within safe operating range.
INPUT=$(cat)

NEW_VALUE=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('input', {})
replace_val = inp.get('new_value', '') or inp.get('replace', '')
for part in replace_val.split('\\n'):
    if 'DB_POOL_SIZE' in part:
        val = part.split('=')[1].strip()
        print(val)
        break
" 2>/dev/null)

if [ -n "$NEW_VALUE" ]; then
    if [ "$NEW_VALUE" -lt 5 ] 2>/dev/null || [ "$NEW_VALUE" -gt 100 ] 2>/dev/null; then
        echo "BLOCKED: DB_POOL_SIZE=$NEW_VALUE is outside safe range (5-100)"
        exit 1
    fi
fi
exit 0
""")

Path("hooks/validate_config_before_deploy.sh").write_text("""\
#!/bin/bash
# Validates that config values are sane before allowing a deploy command.
INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('input', {}).get('command', ''))
" 2>/dev/null)

if echo "$COMMAND" | grep -q "up.*api-server"; then
    CONFIG_FILE="config/api-server.env"
    if [ -f "$CONFIG_FILE" ]; then
        POOL_SIZE=$(grep DB_POOL_SIZE "$CONFIG_FILE" | cut -d= -f2)
        if [ -n "$POOL_SIZE" ] && \
           { [ "$POOL_SIZE" -lt 5 ] 2>/dev/null || \
             [ "$POOL_SIZE" -gt 100 ] 2>/dev/null; }; then
            echo "BLOCKED: Cannot deploy with \
DB_POOL_SIZE=$POOL_SIZE (safe range: 5-100)"
            exit 1
        fi
    fi
fi
exit 0
""")

for hook_file in [
    "hooks/validate_pool_size.sh",
    "hooks/validate_config_before_deploy.sh",
]:
    p = Path(hook_file)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)

print("Infrastructure files generated successfully.")
print()
print("  Created directories: config/, services/, scripts/, hooks/, postmortems/")
print("  Docker Compose:      config/docker-compose.yml")
print("  Prometheus config:   config/prometheus.yml")
print("  API server:          services/api_server.py")
print("  Traffic generator:   scripts/traffic_generator.py")
print(
    "  Safety hooks:        hooks/validate_pool_size.sh,"
    " hooks/validate_config_before_deploy.sh"
)
