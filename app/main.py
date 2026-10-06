from fastapi import FastAPI
from sqlalchemy import text
from app.api.v1.router import api_router
from app.db.session import engine

app = FastAPI(title='Hotel Management System', version= '1.0.0')
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"database": "connected"}
