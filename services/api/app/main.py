from fastapi import FastAPI
from app.api.routes import router
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="jobrunner-api")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
app.include_router(router)