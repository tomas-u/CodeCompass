"""FastAPI backend for mixed language project."""

from fastapi import FastAPI, HTTPException
from models import DataModel


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/data/{item_id}")
def read_item(item_id: int):
    if item_id < 0:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return DataModel(id=item_id, name=f"Item {item_id}")
