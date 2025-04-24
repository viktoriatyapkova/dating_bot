import aio_pika
import os
from dotenv import load_dotenv

load_dotenv()

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))

async def get_rabbit_connection():
    return await aio_pika.connect_robust(
        host=RABBIT_HOST,
        port=RABBIT_PORT
    )
