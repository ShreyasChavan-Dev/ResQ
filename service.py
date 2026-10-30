
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from monitoring.monitor import Service, MonitoringEngine
from simulation import router as simulation_router


app = FastAPI(title="ResQ Dashboard")

PROJECT_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(PROJECT_DIR / "templates")
)

app.include_router(simulation_router)


resq = MonitoringEngine()

resq.add_service(
    Service(
        name="Backend",
        health_url="http://127.0.0.1:8001/health",
        app_module="backend_service",
        port=8001
    )
)

resq.add_service(
    Service(
        name="Payment",
        health_url="http://127.0.0.1:8002/health",
        app_module="payment_service",
        port=8002
    )
)

resq.add_dependency(
    service_name="Payment",
    depends_on="Backend"
)


def load_runtime_file(filename, default):

    file_path = PROJECT_DIR / filename

    if not file_path.exists():
        return default

    try:

        with open(file_path, "r") as file:
            return json.load(file)

    except (OSError, ValueError):
        return default


@app.get("/")
def dashboard(request: Request):

    for service in resq.services.values():
        resq.check_health(service)

    data = resq.get_dashboard_data()

    runtime_stats = load_runtime_file(
        "resq_runtime_stats.json",
        {}
    )

    for key in [
        "total_failures",
        "successful_recoveries",
        "failed_recoveries",
        "blocked_recoveries",
        "success_rate"
    ]:

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

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=data
    )


@app.get("/health")
def dashboard_health():

    return {
        "service": "ResQ Dashboard",
        "status": "healthy"
    }


@app.get("/api/dashboard")
def dashboard_api():

    for service in resq.services.values():
        resq.check_health(service)

    data = resq.get_dashboard_data()

    data["event_history"] = load_runtime_file(
        "resq_event_history.json",
        []
    )

    return data
