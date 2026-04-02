from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield


app = FastAPI(title="Knowledge Base Service", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!doctype html>
<html>
<head><title>Knowledge Base Service</title></head>
<body><h1>Knowledge Base Service</h1></body>
</html>"""
