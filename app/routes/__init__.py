from fastapi import FastAPI

from .get_results_route import parse_router


def register_routes(app: FastAPI):
    app.include_router(parse_router, prefix="/api", tags=["Parses"])
