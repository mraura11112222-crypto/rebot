import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI

from app.bot import start_bot

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "bot is running"}


async def main():
    port = int(os.environ.get("PORT", 10000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
