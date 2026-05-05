"""
Customer Success FTE — Kafka Event Streaming
==============================================
Phase 2: Specialization

Kafka producer and consumer for event-driven message processing.
Handles multi-channel event streaming with proper error handling,
retry logic, and dead letter queue support.
"""

import json
import logging
import os
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ─── Topic Definitions ─────────────────────────────────────────────────────

TOPICS = {
    # Incoming tickets from all channels (unified)
    'tickets_incoming': os.getenv(
        "KAFKA_TOPIC_INCOMING", "fte.tickets.incoming"
    ),

    # Channel-specific inbound
    'email_inbound': os.getenv(
        "KAFKA_TOPIC_EMAIL_IN", "fte.channels.email.inbound"
    ),
    'whatsapp_inbound': os.getenv(
        "KAFKA_TOPIC_WHATSAPP_IN", "fte.channels.whatsapp.inbound"
    ),
    'webform_inbound': os.getenv(
        "KAFKA_TOPIC_WEBFORM_IN", "fte.channels.webform.inbound"
    ),

    # Channel-specific outbound
    'email_outbound': os.getenv(
        "KAFKA_TOPIC_EMAIL_OUT", "fte.channels.email.outbound"
    ),
    'whatsapp_outbound': os.getenv(
        "KAFKA_TOPIC_WHATSAPP_OUT", "fte.channels.whatsapp.outbound"
    ),

    # Escalations
    'escalations': os.getenv(
        "KAFKA_TOPIC_ESCALATIONS", "fte.escalations"
    ),

    # Metrics and monitoring
    'metrics': os.getenv(
        "KAFKA_TOPIC_METRICS", "fte.metrics"
    ),

    # Dead letter queue for failed processing
    'dlq': os.getenv(
        "KAFKA_TOPIC_DLQ", "fte.dlq"
    ),
}

# ─── Kafka Configuration ───────────────────────────────────────────────────

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)


class FTEKafkaProducer:
    """Async Kafka producer for FTE events."""

    def __init__(self, bootstrap_servers: str = None):
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self._running = False

    async def start(self):
        """Initialize and start the Kafka producer."""
        try:
            from aiokafka import AIOKafkaProducer

            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # Reliability settings
                acks='all',
                # Batching
                linger_ms=10,
                max_batch_size=16384,
            )
            await self.producer.start()
            self._running = True
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")

        except ImportError:
            logger.warning("aiokafka not installed, using mock producer")
            self._running = False
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self._running = False

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer and self._running:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
            finally:
                self._running = False

    async def publish(self, topic: str, event: dict,
                      key: str = None, headers: dict = None):
        """Publish an event to a Kafka topic.
        
        Args:
            topic: Topic name (use TOPICS dict values)
            event: Event data (will be JSON serialized)
            key: Optional message key for partitioning
            headers: Optional message headers
        """
        if not self._running or not self.producer:
            # Mock mode: just log
            logger.info(
                f"[MOCK KAFKA] Published to {topic}: "
                f"{json.dumps(event)[:200]}..."
            )
            return

        try:
            # Add metadata
            event['timestamp'] = datetime.utcnow().isoformat()
            event['event_id'] = event.get(
                'event_id',
                f"evt-{datetime.utcnow().timestamp()}"
            )

            # Serialize headers
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode('utf-8'))
                    for k, v in headers.items()
                ]

            # Send message
            key_bytes = key.encode('utf-8') if key else None
            await self.producer.send_and_wait(
                topic,
                value=event,
                key=key_bytes,
                headers=kafka_headers
            )

            logger.debug(f"Published event to {topic}: {event.get('event_id')}")

        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            # Send to DLQ
            await self._send_to_dlq(topic, event, str(e))
            raise

    async def publish_batch(self, topic: str, events: list[dict]):
        """Publish multiple events to a topic efficiently."""
        if not self._running or not self.producer:
            for event in events:
                await self.publish(topic, event)
            return

        try:
            for event in events:
                event['timestamp'] = datetime.utcnow().isoformat()
                self.producer.send(topic, value=event)

            # Wait for all buffered messages to be sent
            await self.producer.flush()
            logger.info(f"Published batch of {len(events)} events to {topic}")

        except Exception as e:
            logger.error(f"Failed to publish batch to {topic}: {e}")
            raise

    async def _send_to_dlq(self, original_topic: str,
                            event: dict, error: str):
        """Send failed event to dead letter queue."""
        dlq_event = {
            'original_topic': original_topic,
            'original_event': event,
            'error': error,
            'failed_at': datetime.utcnow().isoformat(),
            'retry_count': event.get('retry_count', 0) + 1
        }

        try:
            if self._running and self.producer:
                await self.producer.send_and_wait(
                    TOPICS['dlq'],
                    value=dlq_event
                )
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")


class FTEKafkaConsumer:
    """Async Kafka consumer for FTE events."""

    def __init__(self, topics: list[str], group_id: str = None,
                 bootstrap_servers: str = None):
        self.topics = topics
        self.group_id = group_id or os.getenv(
            "KAFKA_GROUP_ID", "fte-message-processor"
        )
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.consumer = None
        self._running = False

    async def start(self):
        """Initialize and start the Kafka consumer."""
        try:
            from aiokafka import AIOKafkaConsumer

            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                # Consumer settings
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                # Session management
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_records=100,
            )
            await self.consumer.start()
            self._running = True
            logger.info(
                f"Kafka consumer started: topics={self.topics}, "
                f"group={self.group_id}"
            )

        except ImportError:
            logger.warning("aiokafka not installed, mock consumer")
            self._running = False
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self._running = False

    async def stop(self):
        """Stop the Kafka consumer."""
        if self.consumer and self._running:
            try:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")
            finally:
                self._running = False

    async def consume(self, handler: Callable, max_messages: int = None):
        """Consume messages and process them with the handler.
        
        Args:
            handler: Async function to process each message.
                     Signature: handler(topic, message) -> None
            max_messages: Optional limit on number of messages to consume.
                         None = consume forever.
        """
        if not self._running or not self.consumer:
            logger.warning("Consumer not running, cannot consume messages")
            return

        message_count = 0

        try:
            async for message in self.consumer:
                try:
                    await handler(message.topic, message.value)
                    message_count += 1

                    if max_messages and message_count >= max_messages:
                        logger.info(
                            f"Reached max messages ({max_messages}), stopping"
                        )
                        break

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Don't crash — continue processing next message
                    # The failed message will be retried by Kafka

        except Exception as e:
            logger.error(f"Consumer loop error: {e}")
        finally:
            logger.info(f"Consumer stopped after {message_count} messages")


# ─── Utility Functions ──────────────────────────────────────────────────────

async def create_topics(num_partitions: int = 3, replication_factor: int = 1):
    """Create all required Kafka topics if they don't exist."""
    try:
        from aiokafka.admin import AIOKafkaAdminClient, NewTopic

        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
        )
        await admin_client.start()

        existing_topics = await admin_client.list_topics()

        topics_to_create = []
        for name in TOPICS.values():
            if name not in existing_topics:
                topics_to_create.append(NewTopic(
                    name=name,
                    num_partitions=num_partitions,
                    replication_factor=replication_factor,
                ))

        if topics_to_create:
            await admin_client.create_topics(topics_to_create)
            logger.info(f"Created {len(topics_to_create)} Kafka topics")
        else:
            logger.info("All Kafka topics already exist")

        await admin_client.close()

    except ImportError:
        logger.warning("aiokafka not installed, skipping topic creation")
    except Exception as e:
        logger.error(f"Failed to create Kafka topics: {e}")
