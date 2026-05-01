from fastapi import FastAPI
from app.routes import upload

app = FastAPI()

app.include_router(upload.router)

@app.get("/health")
def read_root():
    return {"message": "Hello from backend!"}
