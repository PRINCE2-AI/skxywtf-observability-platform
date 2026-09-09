import uvicorn

from .config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("observability.api:app", host="127.0.0.1", port=settings.observability_port, reload=False)
