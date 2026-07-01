from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import trip

app = FastAPI(
    title="智能旅行助手",
    description="基于AI的个性化旅行规划服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api/trip", tags=["trip"])


@app.get("/")
async def root():
    return {"message": "智能旅行助手API服务", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
