from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app.auth.routes import router as auth_router
from app.db import TORTOISE_ORM
from app.send.routes import router as send_router

api_router = APIRouter()


@api_router.get("/")
def health():
    return {"status": "ok"}


app = FastAPI()
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)
app.include_router(auth_router)
app.include_router(send_router)


register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=False,  # Aerich handles migrations
    add_exception_handlers=True,
)
