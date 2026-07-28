# GeoCache

GeoCache is a geo-distributed in-memory caching system built to demonstrate how multi-region architectures can reduce network latency and improve data access times for globally distributed web applications.

Instead of serving all user requests from a single centralized database or server, GeoCache simulates a network of regional server nodes located in major global regions (such as US East, EU West, and Asia Pacific). When a client makes a read or write request, the system automatically routes the traffic to the closest server node based on geographic distance, significantly reducing latency.

## Features

- **Location-Based Routing:** Uses the Haversine great-circle distance formula to calculate client-to-server distance and route requests to the nearest optimal node.
- **In-Memory Caching Engine:** Built from scratch using thread-safe data structures, supporting custom Time-To-Live (TTL) expiration and configurable Least Recently Used (LRU) or Least Frequently Used (LFU) eviction policies.
- **Multi-Region Data Replication:** Automatically replicates cache writes across all active regional server nodes so that data remains consistent across the global cluster.
- **WAN Fallback Read-Through:** If a cache miss occurs on the primary regional server, the system checks neighboring regions for the item and backfills the local cache for subsequent requests.
- **Interactive Web Dashboard:** Includes a built-in UI to visualize real-time server health, memory capacity, hit ratios, and simulated location-based request routing.

## System Architecture

The project is designed using a clean, modular backend structure:

1. **Routing Layer (`app/core/geo_router.py`):** Takes client latitude/longitude coordinates (or preset city locations like London, Tokyo, or New York) and computes the distance to all 5 simulated regional server nodes (`us-east`, `eu-west`, `ap-south`, `ap-southeast`, and `sa-east`).
2. **Caching Layer (`app/core/cache_engine.py`):** Each regional server runs an isolated in-memory cache engine wrapped in thread locks for concurrency safety. When the cache reaches its capacity limit, it evicts items based on the selected eviction policy.
3. **Service Layer (`app/services/data_service.py`):** Coordinates data storage, cross-region asynchronous replication, and read-through caching when local misses happen.
4. **API Layer (`app/api/data.py`):** Exposes clean REST endpoints for setting, getting, and evicting cache items, as well as checking live cluster statistics.

## Project Structure

```text
├── app/
│   ├── api/data.py                 # REST API endpoints
│   ├── core/
│   │   ├── cache_engine.py         # Thread-safe LRU/LFU cache implementation
│   │   ├── config.py               # Node locations, coordinates, and default settings
│   │   └── geo_router.py           # Haversine distance calculator and routing logic
│   ├── repositories/
│   │   └── data_repository.py      # Multi-region cluster manager holding cache nodes
│   ├── schemas/data.py             # Pydantic data models and request validation
│   ├── services/data_service.py    # Business logic for routing, replication, and fallback
│   └── main.py                     # FastAPI app initialization and static file mounting
├── static/
│   ├── index.html                  # Interactive demo UI
│   ├── style.css                   # UI styling
│   └── app.js                      # UI event handling and API integration
├── tests/
│   ├── test_api.py                 # End-to-end integration tests
│   ├── test_cache_engine.py        # Unit tests for LRU eviction and TTL expiration
│   └── test_geo_router.py          # Unit tests for distance formula and routing selection
├── Dockerfile                      # Container build instructions
├── docker-compose.yml              # Cluster deployment config
├── requirements.txt                # Python project dependencies
└── pytest.ini                      # Test framework configuration
```

## Getting Started

### 1. Prerequisites
Ensure you have Python 3.10 or higher installed on your system.

### 2. Setup Virtual Environment
Create and activate a local virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Running the Server
Start the local FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

Once running, open your web browser and navigate to:
- **Interactive Demo Dashboard:** `http://localhost:8000`
- **Interactive API Documentation (Swagger):** `http://localhost:8000/docs`

### 4. Running Tests
To verify the cache engine, routing logic, and API endpoints, execute the automated test suite:

```bash
pytest -v
```
