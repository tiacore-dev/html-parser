from fastapi import FastAPI

from .get_results_route import log_router
from .parsing_route import parsing_router


def register_routes(app: FastAPI):
    app.include_router(log_router, prefix="/api", tags=["Logs"])
    app.include_router(parsing_router, prefix="/api", tags=["Parsing"])
