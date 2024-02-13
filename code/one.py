from fastapi import FastAPI
import asyncio
import sys


app = FastAPI()

async def simulate_io_operation():
    await asyncio.sleep(1)

@app.get('/')
async def read_root():
    await simulate_io_operation()
    return {"message":"Hello World!"}

print(sys.path)

# pip install fastapi uvicorn
# uvicorn filename:app -reload