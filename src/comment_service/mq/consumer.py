import json
import logging
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from typing import Dict, Callable, Any
from ..core.config import Settings, load_settings

logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.connection: AbstractRobustConnection = None
        self.channel: aio_pika.abc.AbstractChannel = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
            self.channel = await self.connection.channel()

            await self.channel.set_qos(prefetch_count=10)

            logger.info("Event consumer connected to RabbitMQ successfully")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        self.handlers[event_type] = handler
        logger.debug(f"Handler registered for event type: {event_type}")

    async def start_consuming(self, queue_name: str = "comments_events"):
        if not self.channel:
            await self.connect()

        exchange = await self.channel.declare_exchange(
            "blog_events",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dead_letters",
                "x-dead-letter-routing-key": "comments_events_dl"
            }
        )

        await queue.bind(exchange, "comments.*")
        
        # Также биндим на возможные события от других сервисов
        # Например, если нужно слушать события постов или профилей
        await queue.bind(exchange, "posts.deleted")
        await queue.bind(exchange, "posts.post_deleted")

        logger.info(f"Started consuming from queue: {queue_name}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        event_data = json.loads(message.body.decode())
                        routing_key = message.routing_key or ""
                        
                        # Определяем тип события по routing_key или по event_type в теле сообщения
                        if routing_key.startswith("comments."):
                            event_type = event_data.get("event_type")
                        elif routing_key == "posts.deleted" or routing_key == "posts.post_deleted":
                            event_type = "post_deleted"
                        else:
                            event_type = event_data.get("event_type")

                        if event_type and event_type in self.handlers:
                            await self.handlers[event_type](event_data)
                            logger.debug(f"Event processed: {event_type} (routing_key: {routing_key})")
                        else:
                            logger.warning(f"No handler for event type: {event_type} (routing_key: {routing_key})")

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Message will be rejected and go to DLQ

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Event consumer connection closed")

