
# ResQ - Intelligent Service Monitoring and Automatic Recovery

ResQ is a Python-based service monitoring and automatic recovery system designed to detect service failures, manage recovery attempts, and restore dependent services in the correct order.

## Features

- **Real-Time Health Monitoring:** Monitors registered services using HTTP health endpoints.
- **Automatic Failure Detection:** Detects when a monitored service becomes unhealthy.
- **Automatic Recovery:** Attempts to restart failed services.
- **Dependency-Aware Recovery:** Restores dependent services in the correct order.
- **Intelligent Recovery Protection:** Limits repeated recovery attempts and applies cooldown periods.
- **Event History:** Records service failures and recovery events.
- **Live Dashboard:** Displays service health, recovery statistics, dependencies, and event history.
- **Failure Simulation:** Allows testing service failures through the dashboard.
- **Automated Testing:** Includes unit tests for recovery protection and dependency management.

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Requests
- HTML
- CSS
- JavaScript
- Unittest

## Project Architecture

```text
ResQ/
│
├── main.py
├── service.py
├── backend_service.py
├── payment_service.py
├── simulation.py
│
├── monitoring/
│   ├── __init__.py
│   ├── monitor.py
│   └── health_checker.py
│
├── recovery/
│   ├── __init__.py
│   └── recovery_manager.py
│
├── dependency/
│   ├── __init__.py
│   └── dependency_graph.py
│
├── tests/
│   ├── test_recovery_manager.py
│   └── test_dependency_graph.py
│
├── templates/
│   └── index.html
│
├── config/
│   └── settings.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## How It Works

1. ResQ continuously checks the health endpoints of registered services.
2. When a service fails, ResQ detects the failure.
3. The dependency graph determines the correct recovery order.
4. The recovery manager checks attempt limits and cooldown restrictions.
5. ResQ attempts to restart the failed service.
6. The health endpoint is checked again to verify recovery.
7. Events and statistics are saved for dashboard display.

## Running the Project

### Requirements

- Python 3.10 or newer
- Windows for the current failure simulation and automatic process restart implementation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Backend Service

```bash
python -m uvicorn backend_service:app --host 127.0.0.1 --port 8001
```

### Start Payment Service

```bash
python -m uvicorn payment_service:app --host 127.0.0.1 --port 8002
```

### Start ResQ Monitoring Engine

```bash
python main.py
```

### Start Dashboard

```bash
python -m uvicorn service:app --host 127.0.0.1 --port 8000
```

Open the dashboard:

http://127.0.0.1:8000

Each command should run in a separate terminal.

## Running Automated Tests

Run all tests using:

```bash
python -m unittest discover -s tests -v
```

The tests cover:

- Initial recovery permission
- Recovery cooldown
- Maximum recovery attempts
- Recovery statistics
- Dependency registration
- Correct recovery order
- Circular dependency detection

## Current Project Scope

ResQ is currently a local prototype monitoring two FastAPI services.

The recovery and process-management implementation is designed for the current Windows test environment. Production deployment would require additional features such as distributed monitoring, persistent storage, authentication, security controls, and cross-platform process management.

## Future Enhancements

- Docker-based service management
- Distributed monitoring
- Database-backed event history
- Email and alert notifications
- More service integrations
- Advanced failure prediction
- Authentication and role-based access
- Cloud deployment

## Project Goal

To demonstrate intelligent service monitoring, automated failure detection, dependency-aware recovery, and fault-tolerant system design using Python.
