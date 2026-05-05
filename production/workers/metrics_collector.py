"""
Customer Success FTE — Metrics Collector Worker
================================================
Phase 2: Specialization

Background worker that continuously collects, aggregates, and stores
performance metrics for the Customer Success FTE system.

Metrics collected:
- Per-channel message throughput (email, WhatsApp, web_form)
- Agent response latency (P50, P95, P99)
- Escalation rate by channel and reason
- Sentiment distribution (positive / neutral / negative)
- Ticket resolution rate and average time-to-resolve
- Error rate and dead-letter-queue depth
- Knowledge-base hit/miss rate
- 24/7 uptime heartbeat

Alerts generated when:
- Error rate > 5% over 5 minutes
- P95 latency > 3 000 ms
- Escalation rate > 25%
- Sentiment average < 0.35 (sustained negative)
- DLQ depth > 10 unprocessed messages
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Alert Thresholds ──────────────────────────────────────────────────────

ALERT_THRESHOLDS = {
    "error_rate_pct": 5.0,          # > 5 % errors in last 5 min
    "p95_latency_ms": 3_000,        # > 3 s P95 response latency
    "escalation_rate_pct": 25.0,    # > 25 % of tickets escalated
    "avg_sentiment_min": 0.35,      # sustained negative sentiment
    "dlq_depth_max": 10,            # > 10 items in dead-letter queue
}

COLLECTION_INTERVAL_SECONDS = 60   # collect every minute
HEARTBEAT_INTERVAL_SECONDS = 30    # uptime heartbeat every 30 s
WINDOW_MINUTES = 5                  # rolling window for rate calculations


class MetricsCollector:
    """
    Background worker that collects and records system-wide metrics.

    Usage (started alongside UnifiedMessageProcessor in workers/main):
        collector = MetricsCollector()
        await collector.start()        # blocks — run via asyncio.gather
    """

    def __init__(self):
        self._running = False

        # Rolling in-memory buffers (last WINDOW_MINUTES of data)
        self._latencies: deque = deque(maxlen=10_000)
        self._message_counts: dict = defaultdict(int)      # channel → count
        self._error_counts: dict = defaultdict(int)        # channel → count
        self._escalation_counts: dict = defaultdict(int)   # reason  → count
        self._sentiments: deque = deque(maxlen=1_000)
        self._dlq_depth: int = 0

        # Kafka producer (optional — falls back gracefully)
        self._producer = None

    # ─── Lifecycle ─────────────────────────────────────────────────────────

    async def start(self):
        """Start all background collection loops."""
        self._running = True
        logger.info("MetricsCollector started")

        try:
            from production.kafka_client import FTEKafkaProducer
            self._producer = FTEKafkaProducer()
            await self._producer.start()
        except Exception as e:
            logger.warning(f"MetricsCollector: Kafka not available ({e}) — metrics will be DB-only")

        await asyncio.gather(
            self._collection_loop(),
            self._heartbeat_loop(),
        )

    async def stop(self):
        """Gracefully stop the collector."""
        self._running = False
        if self._producer:
            try:
                await self._producer.stop()
            except Exception:
                pass
        logger.info("MetricsCollector stopped")

    # ─── Public Recording API (called by message_processor) ────────────────

    def record_message(self, channel: str, latency_ms: int,
                       escalated: bool, sentiment_score: float,
                       error: bool = False):
        """
        Record a single processed message event.

        Called by UnifiedMessageProcessor after each message is handled so
        that metrics are captured in real-time without an extra DB round-trip.

        Args:
            channel: Source channel (email / whatsapp / web_form)
            latency_ms: End-to-end processing time in milliseconds
            escalated: Whether the message was escalated to a human
            sentiment_score: Sentiment score 0.0–1.0
            error: Whether processing raised an exception
        """
        self._message_counts[channel] += 1
        self._latencies.append(latency_ms)
        self._sentiments.append(sentiment_score)
        if escalated:
            self._escalation_counts[channel] += 1
        if error:
            self._error_counts[channel] += 1

    def record_escalation(self, reason: str):
        """Record an escalation event by reason for detailed reporting."""
        self._escalation_counts[f"reason:{reason}"] += 1

    def record_dlq_event(self):
        """Increment the DLQ depth counter."""
        self._dlq_depth += 1

    def record_dlq_processed(self):
        """Decrement the DLQ depth counter when an item is resolved."""
        if self._dlq_depth > 0:
            self._dlq_depth -= 1

    # ─── Collection Loop ───────────────────────────────────────────────────

    async def _collection_loop(self):
        """Main metrics collection loop — runs every COLLECTION_INTERVAL_SECONDS."""
        while self._running:
            try:
                await self._collect_and_store()
            except Exception as e:
                logger.error(f"MetricsCollector._collection_loop error: {e}", exc_info=True)
            await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)

    async def _collect_and_store(self):
        """Collect all metrics, persist to DB, publish to Kafka, check alerts."""
        snapshot = self._build_snapshot()

        # Persist to PostgreSQL
        await self._persist_metrics(snapshot)

        # Publish summary to Kafka fte.metrics topic
        await self._publish_to_kafka(snapshot)

        # Run alert checks
        await self._check_alerts(snapshot)

        logger.info(
            f"[Metrics] msgs={snapshot['total_messages']} "
            f"p95={snapshot['p95_latency_ms']}ms "
            f"escalation={snapshot['escalation_rate_pct']:.1f}% "
            f"sentiment={snapshot['avg_sentiment']:.2f} "
            f"errors={snapshot['error_rate_pct']:.1f}%"
        )

    def _build_snapshot(self) -> dict:
        """Build a point-in-time metrics snapshot from in-memory buffers."""
        now = datetime.utcnow()

        total_messages = sum(self._message_counts.values())
        total_errors = sum(self._error_counts.values())
        total_escalations = sum(
            v for k, v in self._escalation_counts.items()
            if not k.startswith("reason:")
        )

        # Latency percentiles
        sorted_latencies = sorted(self._latencies) if self._latencies else [0]
        p50 = _percentile(sorted_latencies, 50)
        p95 = _percentile(sorted_latencies, 95)
        p99 = _percentile(sorted_latencies, 99)
        avg_latency = sum(sorted_latencies) / len(sorted_latencies)

        # Rates
        error_rate = (total_errors / total_messages * 100) if total_messages else 0.0
        escalation_rate = (total_escalations / total_messages * 100) if total_messages else 0.0

        # Sentiment
        avg_sentiment = (
            sum(self._sentiments) / len(self._sentiments)
            if self._sentiments else 0.5
        )
        negative_count = sum(1 for s in self._sentiments if s < 0.4)
        positive_count = sum(1 for s in self._sentiments if s >= 0.7)
        neutral_count = len(self._sentiments) - negative_count - positive_count

        # Per-channel breakdown
        channel_breakdown = {
            ch: {
                "messages": self._message_counts.get(ch, 0),
                "escalations": self._escalation_counts.get(ch, 0),
                "errors": self._error_counts.get(ch, 0),
            }
            for ch in ["email", "whatsapp", "web_form"]
        }

        # Top escalation reasons
        reasons = {
            k.replace("reason:", ""): v
            for k, v in self._escalation_counts.items()
            if k.startswith("reason:")
        }
        top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "recorded_at": now.isoformat(),
            "window_minutes": WINDOW_MINUTES,
            # Throughput
            "total_messages": total_messages,
            "total_errors": total_errors,
            "total_escalations": total_escalations,
            # Latency
            "avg_latency_ms": round(avg_latency),
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            # Rates
            "error_rate_pct": round(error_rate, 2),
            "escalation_rate_pct": round(escalation_rate, 2),
            # Sentiment
            "avg_sentiment": round(avg_sentiment, 3),
            "sentiment_positive": positive_count,
            "sentiment_neutral": neutral_count,
            "sentiment_negative": negative_count,
            # Per channel
            "channel_breakdown": channel_breakdown,
            # Top escalation reasons
            "top_escalation_reasons": top_reasons,
            # DLQ
            "dlq_depth": self._dlq_depth,
        }

    # ─── Persistence ───────────────────────────────────────────────────────

    async def _persist_metrics(self, snapshot: dict):
        """Write key metrics to the agent_metrics table in PostgreSQL."""
        try:
            from production.database.queries import record_metric

            metrics_to_write = [
                ("total_messages", snapshot["total_messages"], None),
                ("avg_latency_ms", snapshot["avg_latency_ms"], None),
                ("p95_latency_ms", snapshot["p95_latency_ms"], None),
                ("p99_latency_ms", snapshot["p99_latency_ms"], None),
                ("error_rate_pct", snapshot["error_rate_pct"], None),
                ("escalation_rate_pct", snapshot["escalation_rate_pct"], None),
                ("avg_sentiment", snapshot["avg_sentiment"], None),
                ("dlq_depth", snapshot["dlq_depth"], None),
            ]

            # Per-channel message counts
            for channel, data in snapshot["channel_breakdown"].items():
                metrics_to_write.append(
                    ("messages_total", data["messages"], channel)
                )
                metrics_to_write.append(
                    ("escalations_total", data["escalations"], channel)
                )
                metrics_to_write.append(
                    ("errors_total", data["errors"], channel)
                )

            for name, value, channel in metrics_to_write:
                await record_metric(
                    metric_name=name,
                    metric_value=float(value),
                    channel=channel,
                    dimensions={"window_minutes": WINDOW_MINUTES},
                )

        except Exception as e:
            logger.warning(f"MetricsCollector: failed to persist metrics to DB: {e}")

    async def _publish_to_kafka(self, snapshot: dict):
        """Publish metrics snapshot to fte.metrics Kafka topic."""
        if not self._producer:
            return
        try:
            from production.kafka_client import TOPICS
            await self._producer.publish(
                TOPICS["metrics"],
                {
                    "event_type": "metrics_snapshot",
                    **snapshot,
                }
            )
        except Exception as e:
            logger.warning(f"MetricsCollector: failed to publish metrics to Kafka: {e}")

    # ─── Alert Checks ──────────────────────────────────────────────────────

    async def _check_alerts(self, snapshot: dict):
        """Check metrics against alert thresholds and log/publish alerts."""
        alerts = []

        if snapshot["error_rate_pct"] > ALERT_THRESHOLDS["error_rate_pct"]:
            alerts.append({
                "type": "HIGH_ERROR_RATE",
                "severity": "critical",
                "message": (
                    f"Error rate {snapshot['error_rate_pct']:.1f}% exceeds "
                    f"threshold {ALERT_THRESHOLDS['error_rate_pct']}%"
                ),
                "value": snapshot["error_rate_pct"],
            })

        if snapshot["p95_latency_ms"] > ALERT_THRESHOLDS["p95_latency_ms"]:
            alerts.append({
                "type": "HIGH_LATENCY",
                "severity": "warning",
                "message": (
                    f"P95 latency {snapshot['p95_latency_ms']}ms exceeds "
                    f"threshold {ALERT_THRESHOLDS['p95_latency_ms']}ms"
                ),
                "value": snapshot["p95_latency_ms"],
            })

        if snapshot["escalation_rate_pct"] > ALERT_THRESHOLDS["escalation_rate_pct"]:
            alerts.append({
                "type": "HIGH_ESCALATION_RATE",
                "severity": "warning",
                "message": (
                    f"Escalation rate {snapshot['escalation_rate_pct']:.1f}% exceeds "
                    f"threshold {ALERT_THRESHOLDS['escalation_rate_pct']}%"
                ),
                "value": snapshot["escalation_rate_pct"],
            })

        if snapshot["avg_sentiment"] < ALERT_THRESHOLDS["avg_sentiment_min"]:
            alerts.append({
                "type": "LOW_SENTIMENT",
                "severity": "warning",
                "message": (
                    f"Average sentiment {snapshot['avg_sentiment']:.2f} is below "
                    f"threshold {ALERT_THRESHOLDS['avg_sentiment_min']}"
                ),
                "value": snapshot["avg_sentiment"],
            })

        if snapshot["dlq_depth"] > ALERT_THRESHOLDS["dlq_depth_max"]:
            alerts.append({
                "type": "HIGH_DLQ_DEPTH",
                "severity": "critical",
                "message": (
                    f"DLQ depth {snapshot['dlq_depth']} exceeds "
                    f"threshold {ALERT_THRESHOLDS['dlq_depth_max']}"
                ),
                "value": snapshot["dlq_depth"],
            })

        for alert in alerts:
            logger.warning(
                f"[ALERT] {alert['type']} ({alert['severity'].upper()}): "
                f"{alert['message']}"
            )
            await self._publish_alert(alert, snapshot["recorded_at"])

    async def _publish_alert(self, alert: dict, recorded_at: str):
        """Publish an alert event to the escalations Kafka topic."""
        if not self._producer:
            return
        try:
            from production.kafka_client import TOPICS
            await self._producer.publish(
                TOPICS["escalations"],
                {
                    "event_type": "metrics_alert",
                    "alert_type": alert["type"],
                    "severity": alert["severity"],
                    "message": alert["message"],
                    "value": alert["value"],
                    "recorded_at": recorded_at,
                    "requires_human": alert["severity"] == "critical",
                }
            )
        except Exception as e:
            logger.warning(f"MetricsCollector: failed to publish alert: {e}")

    # ─── Heartbeat Loop ────────────────────────────────────────────────────

    async def _heartbeat_loop(self):
        """
        Publish a liveness heartbeat every HEARTBEAT_INTERVAL_SECONDS.

        This allows external monitoring (Prometheus, Grafana, k8s probes)
        to verify the worker is alive without requiring a database query.
        """
        while self._running:
            try:
                await self._publish_heartbeat()
            except Exception as e:
                logger.error(f"MetricsCollector._heartbeat_loop error: {e}")
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)

    async def _publish_heartbeat(self):
        """Publish a lightweight heartbeat event."""
        if not self._producer:
            logger.debug("[MetricsCollector] heartbeat (Kafka unavailable — log only)")
            return
        try:
            from production.kafka_client import TOPICS
            await self._producer.publish(
                TOPICS["metrics"],
                {
                    "event_type": "worker_heartbeat",
                    "worker": "metrics_collector",
                    "status": "alive",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_messages_seen": sum(self._message_counts.values()),
                }
            )
        except Exception as e:
            logger.warning(f"MetricsCollector: heartbeat publish failed: {e}")


# ─── Helpers ──────────────────────────────────────────────────────────────

def _percentile(sorted_data: list, pct: int) -> int:
    """Return the given percentile value from a pre-sorted list."""
    if not sorted_data:
        return 0
    idx = max(0, int(len(sorted_data) * pct / 100) - 1)
    return sorted_data[idx]
