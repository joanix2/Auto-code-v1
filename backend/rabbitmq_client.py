"""
RabbitMQ integration module.
Handles message queue operations for task distribution.
"""
import json
import pika
import logging
from typing import Dict, Any, Callable
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client for publishing and consuming messages"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = config.RABBITMQ_QUEUE
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                config.RABBITMQ_USER,
                config.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logger.info(f"Connected to RabbitMQ at {config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task to the queue
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.channel:
                self.connect()
                
            message = json.dumps(task_data)
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            logger.info(f"Published task: {task_data.get('ticket_id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            return False
    
    def consume_tasks(self, callback: Callable):
        """
        Start consuming tasks from the queue
        
        Args:
            callback: Function to call when a message is received
        """
        try:
            if not self.channel:
                self.connect()
            
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback
            )
            
            logger.info(f"Started consuming from queue: {self.queue_name}")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.stop()
        except Exception as e:
            logger.error(f"Error consuming tasks: {e}")
            raise
    
    def stop(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Global instance
rabbitmq_client = RabbitMQClient()
