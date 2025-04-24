import json
from aio_pika import IncomingMessage
from app.rabbit.connection import get_rabbit_connection

QUEUE_NAME = "profiles"

async def get_next_profile() -> dict | None:
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    message: IncomingMessage = await queue.get(no_ack=True, fail=False)
    await connection.close()
    if message:
        return json.loads(message.body.decode())
    return None
