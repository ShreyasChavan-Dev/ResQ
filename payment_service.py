
from fastapi import FastAPI

app = FastAPI(title="ResQ Payment Service")


@app.get("/")
def home():
    return {
        "service": "Payment",
        "message": "Payment service is running"
    }


@app.get("/health")
def health():
    return {
        "service": "Payment",
        "status": "healthy"
    }

