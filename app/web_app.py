from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise

from app.routes import register_routes


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("🔥 Lifespan START")

        from app.database.config import TORTOISE_ORM

        await Tortoise.init(config=TORTOISE_ORM)

        Tortoise.init_models(["app.database.models"], "models")
        await Tortoise.generate_schemas()

        yield

        await Tortoise.close_connections()

    app = FastAPI(title="MK Parser", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routes(app)

    return app
