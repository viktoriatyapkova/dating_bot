import json
from aio_pika import Message
from app.rabbit.connection import get_rabbit_connection

QUEUE_NAME = "profiles"

async def publish_profile(profile: dict):
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    await channel.declare_queue(QUEUE_NAME, durable=True)

    message = Message(body=json.dumps(profile).encode())
    await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)
    await connection.close()
