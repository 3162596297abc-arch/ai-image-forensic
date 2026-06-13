



import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, HOST, PORT
from routers.analyze import router as analyze_router

app = FastAPI(
    title="AI Visual Authenticity System",
    description="未来AI视觉真实性分析系统 - API",
    version="3.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    uvicorn.run(app, host=HOST, port=PORT, timeout_keep_alive=90)

