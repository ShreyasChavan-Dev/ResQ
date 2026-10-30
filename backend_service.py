from fastapi import FastAPI

app = FastAPI(title="ResQ Backend Service")


@app.get("/")
def home():
    return {
        "service": "Backend",
        "message": "Backend service is running"
    }


@app.get("/health")
def health():
    return {
        "service": "Backend",
        "status": "healthy"
    }
