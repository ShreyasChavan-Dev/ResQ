
import subprocess
import sys

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/simulation")


SERVICE_PORTS = {
    "Backend": 8001,
    "Payment": 8002
}


@router.post("/failure/{service_name}")
def simulate_failure(service_name: str):

    service_name = service_name.capitalize()

    if service_name not in SERVICE_PORTS:

        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    port = SERVICE_PORTS[service_name]

    if sys.platform != "win32":

        raise HTTPException(
            status_code=500,
            detail="This simulation currently supports Windows only."
        )

    try:

        command = (
            f"$connections = Get-NetTCPConnection "
            f"-LocalPort {port} "
            f"-State Listen "
            f"-ErrorAction SilentlyContinue; "
            f"if ($connections) {{ "
            f"$connections | ForEach-Object "
            f"{{ Stop-Process -Id $_.OwningProcess -Force }} "
            f"}} else {{ exit 2 }}"
        )

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                command
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:

            raise HTTPException(
                status_code=409,
                detail="Service is not running or could not be stopped."
            )

        return {
            "service": service_name,
            "status": "failure_simulated",
            "message": (
                f"{service_name} was stopped successfully. "
                "ResQ should detect the failure."
            )
        }

    except subprocess.TimeoutExpired:

        raise HTTPException(
            status_code=500,
            detail="Simulation command timed out."
        )
