
from fastapi import APIRouter, HTTPException
import docker
from docker.errors import DockerException, NotFound


router = APIRouter()

# Only these two containers can be stopped by the simulator.
SERVICE_CONTAINERS = {
    "backend": "resq-backend",
    "payment": "resq-payment"
}


@router.post("/simulate-failure/{service_name}")
def simulate_failure(service_name: str):
    """
    Simulate a service failure by stopping its Docker container.

    The ResQ monitor should detect the failure and restart
    the container according to its recovery rules.
    """

    service_name = service_name.lower().strip()

    if service_name not in SERVICE_CONTAINERS:
        raise HTTPException(
            status_code=400,
            detail="Unknown service. Use backend or payment."
        )

    container_name = SERVICE_CONTAINERS[service_name]

    try:
        client = docker.from_env()

        container = client.containers.get(container_name)

        if container.status == "running":
            container.stop(timeout=5)

            return {
                "success": True,
                "service": service_name,
                "container": container_name,
                "message": (
                    f"Failure simulated for {service_name}. "
                    "ResQ will detect and attempt recovery."
                )
            }

        raise HTTPException(
            status_code=409,
            detail=f"{container_name} is not running."
        )

    except NotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Docker container {container_name} was not found."
        )

    except DockerException as error:
        raise HTTPException(
            status_code=503,
            detail=f"Docker operation failed: {error}"
        )


@router.get("/simulation/health")
def simulation_health():
    """Check whether the simulation API is available."""

    return {
        "service": "ResQ Failure Simulation",
        "status": "healthy"
    }
