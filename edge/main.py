from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# MQTT
from mqtt import start_mqtt, stop_mqtt, mqtt_client

app = FastAPI(
    title="Smart Home Edge API",
    description="Local Smart Home Backend (No Internet)",
    version="1.0.0"
)

# =========================
# CORS (عشان Flutter + Dashboard)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # لاحقًا نخصصها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MQTT INIT
# =========================

@app.on_event("startup")
def startup_event():
    print("🚀 Starting Smart Home Backend...")
    start_mqtt()
    print("📡 MQTT Connected & Subscribed")

@app.on_event("shutdown")
def shutdown_event():
    print("🛑 Shutting down system...")
    stop_mqtt()

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def home():
    return {
        "status": "running",
        "system": "Smart Home Edge Backend",
        "mode": "LOCAL"
    }

@app.get("/health")
def health():
    return {
        "mqtt": mqtt_client.is_connected(),
        "server": "ok"
    }