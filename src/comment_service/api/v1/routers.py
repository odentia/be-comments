from fastapi import APIRouter

from comment_service.api.v1.comments_router import post_router, game_router

api_v1 = APIRouter(prefix="/v1", tags=["v1"])
api_v1.include_router(post_router)
api_v1.include_router(game_router)


@api_v1.get("/healthz")
async def healthz():
    return {"status": "ok"}
