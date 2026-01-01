"""RabbitMQ Service - Send and consume messages from RabbitMQ queue"""
import pika
import json
import logging
from typing import Dict, Any, Callable
from src.utils.config import config

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service to interact with RabbitMQ"""
    
    def __init__(self):
        self.host = config.RABBITMQ_HOST
        self.port = config.RABBITMQ_PORT
        self.user = config.RABBITMQ_USER
        self.password = config.RABBITMQ_PASSWORD
        self.queue = config.RABBITMQ_QUEUE
    
    def _get_connection(self):
        """Get RabbitMQ connection"""
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        return pika.BlockingConnection(parameters)
    
    async def send_ticket_to_queue(self, ticket_data: Dict[str, Any], github_token: str):
        """Send ticket to RabbitMQ queue for processing"""
        try:
            connection = self._get_connection()
            channel = connection.channel()
            
            # Declare queue
            channel.queue_declare(queue=self.queue, durable=True)
            
            # Prepare message
            message = {
                "ticket_id": ticket_data.get("id"),
                "title": ticket_data.get("title"),
                "description": ticket_data.get("description"),
                "repository": ticket_data.get("repository"),
                "priority": ticket_data.get("priority"),
                "type": ticket_data.get("type"),
                "github_token": github_token
            }
            
            # Send message
            channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            
            connection.close()
            logger.info(f"✓ Ticket {ticket_data.get('id')} sent to queue '{self.queue}'")
            
        except Exception as e:
            logger.error(f"❌ Failed to send ticket to RabbitMQ: {e}")
            raise


# Singleton instance
rabbitmq_service = RabbitMQService()
