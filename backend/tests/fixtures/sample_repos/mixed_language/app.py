"""Python backend API."""

from fastapi import FastAPI
from typing import Dict


app = FastAPI()


@app.get("/")
def read_root() -> Dict:
    """Root endpoint."""
    return {"message": "Hello World"}


@app.get("/api/data")
def get_data() -> Dict:
    """Get data endpoint."""
    return {"data": [1, 2, 3]}
