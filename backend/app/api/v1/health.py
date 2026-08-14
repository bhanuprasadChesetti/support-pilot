from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def check_health() -> dict[str, str]:
    """Health check endpoint to verify backend system status."""
    return {"status": "ok"}
