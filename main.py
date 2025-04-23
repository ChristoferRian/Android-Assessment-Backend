from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.fast_scan import router as fast_scan_router
from api.full_scan import router as full_scan_router
from api.device_connection import router as device_connection_router
from api.reports import router as reports_router

# Import repositories and services
from repositories.adb_repository import ADBRepository
from repositories.db_repository import DBRepository
from repositories.brand.brand_factory import BrandFactory
from service.device_service import DeviceService
from service.scan_service import ScanService

app = FastAPI(title="Android Assessment Tool API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Create singleton instances of repositories and services
adb_repo = ADBRepository()
db_repo = DBRepository()
brand_factory = BrandFactory(adb_repo)
device_service = DeviceService(adb_repo, brand_factory, websocket_manager=manager)
scan_service = ScanService(adb_repo, db_repo, brand_factory, websocket_manager=manager)

# Store singletons in app.state for dependency injection
app.state.adb_repo = adb_repo
app.state.db_repo = db_repo
app.state.brand_factory = brand_factory
app.state.device_service = device_service
app.state.scan_service = scan_service

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup"""
    await app.state.db_repo.initialize()

# Include routers
app.include_router(device_connection_router, prefix="/device", tags=["Device Connection"])
app.include_router(fast_scan_router, prefix="/scan/fast", tags=["Fast Scan"])
app.include_router(full_scan_router, prefix="/scan/full", tags=["Full Scan"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {"message": "Android Assessment Tool API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
