
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from monitoring.monitor import Service, MonitoringEngine
from simulation import router as simulation_router


app = FastAPI(title="ResQ Dashboard")

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/app/runtime")

templates = Jinja2Templates(
    directory=str(PROJECT_DIR / "templates")
)

app.include_router(simulation_router)


# Dashboard monitoring engine.
# The separate monitor container performs recovery.
resq = MonitoringEngine()

resq.add_service(
    Service(
        name="Backend",
        health_url="http://backend:8001/health",
        app_module="backend_service",
        port=8001
    )
)

resq.add_service(
    Service(
        name="Payment",
        health_url="http://payment:8002/health",
        app_module="payment_service",
        port=8002
    )
)

resq.add_dependency(
    service_name="Payment",
    depends_on="Backend"
)


def load_runtime_file(filename, default):
    """Read shared monitoring data safely."""

    file_path = DATA_DIR / filename

    try:
        if not file_path.exists():
            return default

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        return default


def get_dashboard_data():
    """Collect current service and recovery information."""

    for service in resq.services.values():
        resq.check_health(service)

    data = resq.get_dashboard_data()

    runtime_stats = load_runtime_file(
        "resq_runtime_stats.json",
        {}
    )

    for key in (
        "total_failures",
        "successful_recoveries",
        "failed_recoveries",
        "blocked_recoveries",
        "success_rate"
    ):
        if key in runtime_stats:
            data[key] = runtime_stats[key]

    data["event_history"] = load_runtime_file(
        "resq_event_history.json",
        []
    )

    data["dependency_graph"] = [
        {
            "service": "Backend",
            "dependencies": "None"
        },
        {
            "service": "Payment",
            "dependencies": "Backend"
        }
    ]

    data["recovery_order"] = (
        resq.dependency_graph.get_recovery_order()
    )

    return data


@app.get("/")
def dashboard(request: Request):
    """Render the ResQ dashboard."""

    data = get_dashboard_data()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=data
    )


@app.get("/health")
def dashboard_health():
    """Dashboard container health endpoint."""

    return {
        "service": "ResQ Dashboard",
        "status": "healthy"
    }


@app.get("/api/dashboard")
def dashboard_api():
    """Return dashboard data as JSON."""

    return get_dashboard_data()
