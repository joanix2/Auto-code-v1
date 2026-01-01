"""
Worker agent module.
Consumes tasks from RabbitMQ queue and processes development tasks.
"""
import json
import logging
import time
from typing import Dict, Any
from rabbitmq_client import rabbitmq_client
from github_client import github_client
from agent import DevAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskWorker:
    """Worker that processes development tasks"""
    
    def __init__(self):
        self.agent = DevAgent()
    
    def process_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Process a development task
        
        Args:
            task_data: Task information from queue
            
        Returns:
            bool: True if successful, False otherwise
        """
        ticket_id = task_data.get("ticket_id")
        title = task_data.get("title")
        description = task_data.get("description")
        
        logger.info(f"Processing task for ticket #{ticket_id}: {title}")
        
        try:
            # Update issue status
            github_client.update_issue(
                ticket_id,
                comment="🤖 AI agent started processing this task..."
            )
            
            # Execute the development task
            result = self.agent.execute_task(
                ticket_id=ticket_id,
                title=title,
                description=description
            )
            
            if result["success"]:
                # Update issue with success
                github_client.update_issue(
                    ticket_id,
                    comment=f"✅ Task completed successfully!\n\nPR: {result.get('pr_url', 'N/A')}"
                )
                logger.info(f"Successfully completed task #{ticket_id}")
                return True
            else:
                # Update issue with failure
                github_client.update_issue(
                    ticket_id,
                    comment=f"❌ Task failed: {result.get('error', 'Unknown error')}"
                )
                logger.error(f"Failed to complete task #{ticket_id}: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing task #{ticket_id}: {e}")
            github_client.update_issue(
                ticket_id,
                comment=f"⚠️ Error processing task: {str(e)}"
            )
            return False
    
    def callback(self, ch, method, properties, body):
        """
        Callback function for RabbitMQ message consumption
        
        Args:
            ch: Channel
            method: Method
            properties: Properties
            body: Message body
        """
        try:
            task_data = json.loads(body)
            logger.info(f"Received task: {task_data.get('ticket_id')}")
            
            # Process the task
            success = self.process_task(task_data)
            
            if success:
                # Acknowledge the message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Task acknowledged: {task_data.get('ticket_id')}")
            else:
                # Reject and requeue for retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning(f"Task requeued: {task_data.get('ticket_id')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge invalid message
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Start the worker"""
        logger.info("Starting task worker...")
        rabbitmq_client.consume_tasks(self.callback)


if __name__ == "__main__":
    worker = TaskWorker()
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
