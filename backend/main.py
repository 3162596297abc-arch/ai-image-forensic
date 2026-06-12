



import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from routers.analyze import router as analyze_router

app = FastAPI(
    title="AI Visual Authenticity System",
    description="未来AI视觉真实性分析系统 - API",
    version="3.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/")
async def root():
    return {
        "system": "AI Visual Authenticity System",
        "status": "online",
        "version": "3.2.0",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, timeout_keep_alive=90)

