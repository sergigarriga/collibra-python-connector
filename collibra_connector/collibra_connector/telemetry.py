"""
OpenTelemetry integration for Collibra Connector.

This module provides observability capabilities including:
- Distributed tracing for API calls
- Metrics for request latency and error rates
- Automatic instrumentation of all API operations

Example:
    >>> from collibra_connector import CollibraConnector
    >>> from collibra_connector.telemetry import enable_telemetry
    >>>
    >>> # Enable telemetry with OTLP exporter
    >>> enable_telemetry(
    ...     service_name="my-data-pipeline",
    ...     otlp_endpoint="http://localhost:4317"
    ... )
    >>>
    >>> # All API calls are now traced
    >>> conn = CollibraConnector(...)
    >>> assets = conn.asset.find_assets()  # Creates a span

For Grafana/Prometheus setup:
    >>> enable_telemetry(
    ...     service_name="collibra-etl",
    ...     otlp_endpoint="http://otel-collector:4317",
    ...     enable_metrics=True
    ... )
"""
from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar, Union

# Check for OpenTelemetry availability
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SpanExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,
        ConsoleMetricExporter,
        MetricExporter,
    )
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.trace import Status, StatusCode, Span
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore
    metrics = None  # type: ignore

# Check for OTLP exporter
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    OTLPSpanExporter = None  # type: ignore
    OTLPMetricExporter = None  # type: ignore


T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Module-level state
_tracer: Optional[Any] = None
_meter: Optional[Any] = None
_enabled: bool = False

# Metrics
_request_counter: Optional[Any] = None
_request_duration: Optional[Any] = None
_error_counter: Optional[Any] = None


def is_telemetry_available() -> bool:
    """Check if OpenTelemetry is installed."""
    return OTEL_AVAILABLE


def is_telemetry_enabled() -> bool:
    """Check if telemetry has been enabled."""
    return _enabled


def enable_telemetry(
    service_name: str = "collibra-connector",
    service_version: str = "1.0.0",
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
    enable_metrics: bool = True,
    custom_resource_attributes: Optional[Dict[str, str]] = None
) -> bool:
    """
    Enable OpenTelemetry instrumentation for the Collibra Connector.

    This function sets up tracing and optionally metrics collection
    for all API calls made through the connector.

    Args:
        service_name: Name of your service for tracing.
        service_version: Version of your service.
        otlp_endpoint: OTLP collector endpoint (e.g., "http://localhost:4317").
        console_export: If True, also export spans to console (for debugging).
        enable_metrics: If True, enable metrics collection.
        custom_resource_attributes: Additional resource attributes.

    Returns:
        True if telemetry was enabled, False if OpenTelemetry is not installed.

    Example:
        >>> # For local development with console output
        >>> enable_telemetry(service_name="my-app", console_export=True)
        >>>
        >>> # For production with OTLP collector
        >>> enable_telemetry(
        ...     service_name="data-pipeline",
        ...     otlp_endpoint="http://otel-collector:4317"
        ... )
    """
    global _tracer, _meter, _enabled
    global _request_counter, _request_duration, _error_counter

    if not OTEL_AVAILABLE:
        logging.warning(
            "OpenTelemetry not installed. Install with: "
            "pip install opentelemetry-api opentelemetry-sdk"
        )
        return False

    # Build resource attributes
    resource_attrs = {
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
    }
    if custom_resource_attributes:
        resource_attrs.update(custom_resource_attributes)

    resource = Resource.create(resource_attrs)

    # Set up tracing
    tracer_provider = TracerProvider(resource=resource)

    # Add exporters
    if otlp_endpoint and OTLP_AVAILABLE:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    elif otlp_endpoint and not OTLP_AVAILABLE:
        logging.warning(
            "OTLP endpoint specified but exporter not installed. "
            "Install with: pip install opentelemetry-exporter-otlp"
        )

    if console_export:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )

    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer("collibra-connector", service_version)

    # Set up metrics
    if enable_metrics:
        metric_readers = []

        if otlp_endpoint and OTLP_AVAILABLE:
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            metric_readers.append(
                PeriodicExportingMetricReader(otlp_metric_exporter)
            )

        if console_export:
            metric_readers.append(
                PeriodicExportingMetricReader(ConsoleMetricExporter())
            )

        if metric_readers:
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=metric_readers
            )
            metrics.set_meter_provider(meter_provider)
            _meter = metrics.get_meter("collibra-connector", service_version)

            # Create metrics
            _request_counter = _meter.create_counter(
                name="collibra_requests_total",
                description="Total number of Collibra API requests",
                unit="1"
            )
            _request_duration = _meter.create_histogram(
                name="collibra_request_duration_seconds",
                description="Duration of Collibra API requests",
                unit="s"
            )
            _error_counter = _meter.create_counter(
                name="collibra_errors_total",
                description="Total number of Collibra API errors",
                unit="1"
            )

    _enabled = True
    logging.info(f"Telemetry enabled for service: {service_name}")
    return True


def disable_telemetry() -> None:
    """Disable telemetry and clean up resources."""
    global _tracer, _meter, _enabled
    global _request_counter, _request_duration, _error_counter

    _tracer = None
    _meter = None
    _request_counter = None
    _request_duration = None
    _error_counter = None
    _enabled = False


@contextmanager
def span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """
    Context manager for creating a traced span.

    Args:
        name: Name of the span.
        attributes: Optional attributes to add to the span.
        record_exception: If True, record exceptions that occur.

    Yields:
        The span object (or None if telemetry not enabled).

    Example:
        >>> with span("process_assets", {"asset_count": 100}) as s:
        ...     # Do work
        ...     s.set_attribute("processed", 100)
    """
    if not _enabled or not _tracer:
        yield None
        return

    with _tracer.start_as_current_span(name) as s:
        if attributes:
            for key, value in attributes.items():
                s.set_attribute(key, value)
        try:
            yield s
        except Exception as e:
            if record_exception:
                s.record_exception(e)
                s.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def traced(
    span_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator for tracing function calls.

    Args:
        span_name: Custom span name (defaults to function name).
        attributes: Static attributes to add to every span.

    Returns:
        Decorated function.

    Example:
        >>> @traced("fetch_customer_data")
        ... def get_customers(limit: int):
        ...     return connector.asset.find_assets(limit=limit)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _enabled or not _tracer:
                return func(*args, **kwargs)

            name = span_name or func.__qualname__
            span_attrs = dict(attributes) if attributes else {}

            # Add function args as attributes (be careful with sensitive data)
            span_attrs["function.name"] = func.__name__
            span_attrs["function.module"] = func.__module__

            start_time = time.time()
            with _tracer.start_as_current_span(name, attributes=span_attrs) as s:
                try:
                    result = func(*args, **kwargs)

                    # Record duration
                    duration = time.time() - start_time
                    s.set_attribute("duration_seconds", duration)

                    # Record metrics
                    if _request_counter:
                        _request_counter.add(
                            1,
                            {"operation": name, "status": "success"}
                        )
                    if _request_duration:
                        _request_duration.record(
                            duration,
                            {"operation": name}
                        )

                    return result

                except Exception as e:
                    s.record_exception(e)
                    s.set_status(Status(StatusCode.ERROR, str(e)))

                    # Record error metric
                    if _error_counter:
                        _error_counter.add(
                            1,
                            {"operation": name, "error_type": type(e).__name__}
                        )

                    raise

        return wrapper  # type: ignore
    return decorator


def traced_async(
    span_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """
    Decorator for tracing async function calls.

    Args:
        span_name: Custom span name (defaults to function name).
        attributes: Static attributes to add to every span.

    Returns:
        Decorated async function.

    Example:
        >>> @traced_async("async_fetch_data")
        ... async def fetch_data():
        ...     return await connector.asset.get_assets_batch(ids)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _enabled or not _tracer:
                return await func(*args, **kwargs)

            name = span_name or func.__qualname__
            span_attrs = dict(attributes) if attributes else {}
            span_attrs["function.name"] = func.__name__
            span_attrs["async"] = True

            start_time = time.time()
            with _tracer.start_as_current_span(name, attributes=span_attrs) as s:
                try:
                    result = await func(*args, **kwargs)

                    duration = time.time() - start_time
                    s.set_attribute("duration_seconds", duration)

                    if _request_counter:
                        _request_counter.add(
                            1,
                            {"operation": name, "status": "success"}
                        )
                    if _request_duration:
                        _request_duration.record(duration, {"operation": name})

                    return result

                except Exception as e:
                    s.record_exception(e)
                    s.set_status(Status(StatusCode.ERROR, str(e)))

                    if _error_counter:
                        _error_counter.add(
                            1,
                            {"operation": name, "error_type": type(e).__name__}
                        )

                    raise

        return wrapper  # type: ignore
    return decorator


class TracedCollibraConnector:
    """
    Wrapper that adds tracing to all CollibraConnector operations.

    This class wraps an existing connector and automatically
    traces all API calls.

    Example:
        >>> from collibra_connector import CollibraConnector
        >>> from collibra_connector.telemetry import TracedCollibraConnector, enable_telemetry
        >>>
        >>> enable_telemetry(service_name="my-app", otlp_endpoint="localhost:4317")
        >>>
        >>> base_conn = CollibraConnector(...)
        >>> conn = TracedCollibraConnector(base_conn)
        >>>
        >>> # All operations are now traced
        >>> assets = conn.asset.find_assets()
    """

    def __init__(self, connector: Any) -> None:
        """
        Initialize traced connector.

        Args:
            connector: The CollibraConnector instance to wrap.
        """
        self._connector = connector
        self._wrapped_apis: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Get wrapped API module with tracing."""
        if name.startswith('_'):
            return getattr(self._connector, name)

        if name in self._wrapped_apis:
            return self._wrapped_apis[name]

        original = getattr(self._connector, name)
        wrapped = TracedAPI(original, name)
        self._wrapped_apis[name] = wrapped
        return wrapped


class TracedAPI:
    """Wrapper that traces all method calls on an API module."""

    def __init__(self, api: Any, api_name: str) -> None:
        self._api = api
        self._api_name = api_name

    def __getattr__(self, name: str) -> Any:
        original = getattr(self._api, name)

        if not callable(original):
            return original

        @functools.wraps(original)
        def traced_method(*args: Any, **kwargs: Any) -> Any:
            span_name = f"collibra.{self._api_name}.{name}"
            attributes = {
                "collibra.api": self._api_name,
                "collibra.method": name,
            }

            # Add some kwargs as attributes (filter sensitive ones)
            safe_kwargs = {
                k: str(v)[:100] for k, v in kwargs.items()
                if k not in ('password', 'token', 'secret', 'auth')
            }
            if safe_kwargs:
                attributes["collibra.params"] = str(safe_kwargs)

            start_time = time.time()

            if not _enabled or not _tracer:
                return original(*args, **kwargs)

            with _tracer.start_as_current_span(span_name, attributes=attributes) as s:
                try:
                    result = original(*args, **kwargs)

                    duration = time.time() - start_time
                    s.set_attribute("duration_seconds", duration)

                    # Add result info
                    if isinstance(result, dict):
                        if "total" in result:
                            s.set_attribute("result.total", result["total"])
                        if "results" in result:
                            s.set_attribute("result.count", len(result["results"]))

                    if _request_counter:
                        _request_counter.add(
                            1,
                            {"api": self._api_name, "method": name, "status": "success"}
                        )
                    if _request_duration:
                        _request_duration.record(
                            duration,
                            {"api": self._api_name, "method": name}
                        )

                    return result

                except Exception as e:
                    s.record_exception(e)
                    s.set_status(Status(StatusCode.ERROR, str(e)))

                    if _error_counter:
                        _error_counter.add(
                            1,
                            {
                                "api": self._api_name,
                                "method": name,
                                "error_type": type(e).__name__
                            }
                        )

                    raise

        return traced_method


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID if in a traced context."""
    if not _enabled or not trace:
        return None

    current_span = trace.get_current_span()
    if current_span:
        return format(current_span.get_span_context().trace_id, '032x')
    return None


def get_current_span_id() -> Optional[str]:
    """Get the current span ID if in a traced context."""
    if not _enabled or not trace:
        return None

    current_span = trace.get_current_span()
    if current_span:
        return format(current_span.get_span_context().span_id, '016x')
    return None


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """Add attributes to the current span."""
    if not _enabled or not trace:
        return

    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def record_exception(exception: Exception) -> None:
    """Record an exception on the current span."""
    if not _enabled or not trace:
        return

    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception)
        current_span.set_status(Status(StatusCode.ERROR, str(exception)))
