import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"response": "Hello I'm athena"}


def start():
    uvicorn.run("athena.main:app", host="0.0.0.0", port=8000, reload=True)
