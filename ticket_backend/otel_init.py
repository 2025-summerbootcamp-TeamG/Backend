# ticket_backend/otel_init.py

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def init_tracing():
    resource = Resource(attributes={
        SERVICE_NAME: "django-backend"
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
