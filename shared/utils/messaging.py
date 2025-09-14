"""
Message queue utilities for inter-service communication
"""
import json
import os
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from uuid import uuid4

import pika
from pika.adapters.blocking_connection import BlockingChannel
from celery import Celery


class MessageQueue:
    """RabbitMQ message queue manager"""
    
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv(
            "RABBITMQ_URL", 
            "amqp://delox:delox_password@localhost:5672/"
        )
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
    
    def disconnect(self):
        """Close connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = "topic"):
        """Declare an exchange"""
        self.connect()
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=True
        )
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue"""
        self.connect()
        self.channel.queue_declare(queue=queue_name, durable=durable)
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Bind queue to exchange with routing key"""
        self.connect()
        self.channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )
    
    def publish_message(
        self,
        exchange_name: str,
        routing_key: str,
        message: Dict[str, Any],
        message_id: str = None
    ):
        """Publish message to exchange"""
        self.connect()
        
        # Add metadata
        message_data = {
            "id": message_id or str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": message
        }
        
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(message_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                message_id=message_data["id"],
                timestamp=int(datetime.utcnow().timestamp())
            )
        )
    
    def consume_messages(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False
    ):
        """Consume messages from queue"""
        self.connect()
        
        def wrapper(ch: BlockingChannel, method, properties, body):
            try:
                message_data = json.loads(body)
                callback(message_data)
                
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapper,
            auto_ack=auto_ack
        )
        
        print(f"Waiting for messages from {queue_name}. To exit press CTRL+C")
        self.channel.start_consuming()


# Celery configuration
def create_celery_app(service_name: str) -> Celery:
    """Create Celery app for background tasks"""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://delox:delox_password@localhost:5672/")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    celery_app = Celery(
        service_name,
        broker=rabbitmq_url,
        backend=redis_url,
        include=[f"{service_name}.tasks"]
    )
    
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
    )
    
    return celery_app


# Event types for inter-service communication
class EventTypes:
    """Standard event types for message routing"""
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    
    # Workspace events
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_DELETED = "workspace.deleted"
    
    # Order events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_ASSIGNED = "order.assigned"
    ORDER_PICKED_UP = "order.picked_up"
    ORDER_DELIVERED = "order.delivered"
    ORDER_FAILED = "order.failed"
    ORDER_CANCELLED = "order.cancelled"
    
    # Courier events
    COURIER_ASSIGNED = "courier.assigned"
    COURIER_LOCATION_UPDATED = "courier.location_updated"
    COURIER_STATUS_CHANGED = "courier.status_changed"
    
    # Route events
    ROUTE_OPTIMIZED = "route.optimized"
    ROUTE_STARTED = "route.started"
    ROUTE_COMPLETED = "route.completed"
    
    # Notification events
    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"


class EventPublisher:
    """High-level event publisher"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.mq = MessageQueue()
        self.exchange_name = "delox.events"
        
        # Declare exchange
        self.mq.declare_exchange(self.exchange_name)
    
    def publish_event(self, event_type: str, data: Dict[str, Any], workspace_id: str = None):
        """Publish domain event"""
        event_data = {
            "service": self.service_name,
            "event_type": event_type,
            "workspace_id": workspace_id,
            "payload": data
        }
        
        routing_key = f"{self.service_name}.{event_type}"
        if workspace_id:
            routing_key = f"{workspace_id}.{routing_key}"
        
        self.mq.publish_message(
            exchange_name=self.exchange_name,
            routing_key=routing_key,
            message=event_data
        )
    
    def close(self):
        """Close message queue connection"""
        self.mq.disconnect()


class EventSubscriber:
    """High-level event subscriber"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.mq = MessageQueue()
        self.exchange_name = "delox.events"
        self.queue_name = f"{service_name}.events"
        
        # Setup queue
        self.mq.declare_exchange(self.exchange_name)
        self.mq.declare_queue(self.queue_name)
    
    def subscribe_to_events(self, event_patterns: list, callback: Callable):
        """Subscribe to specific event patterns"""
        for pattern in event_patterns:
            self.mq.bind_queue(
                queue_name=self.queue_name,
                exchange_name=self.exchange_name,
                routing_key=pattern
            )
        
        self.mq.consume_messages(self.queue_name, callback)
    
    def close(self):
        """Close message queue connection"""
        self.mq.disconnect()


# Global instances
message_queue: Optional[MessageQueue] = None
event_publisher: Optional[EventPublisher] = None


def init_messaging(service_name: str, rabbitmq_url: str = None):
    """Initialize messaging for service"""
    global message_queue, event_publisher
    
    message_queue = MessageQueue(rabbitmq_url)
    event_publisher = EventPublisher(service_name)
    
    return message_queue, event_publisher


def get_event_publisher() -> EventPublisher:
    """Get global event publisher"""
    if event_publisher is None:
        raise RuntimeError("Messaging not initialized. Call init_messaging() first.")
    return event_publisher
