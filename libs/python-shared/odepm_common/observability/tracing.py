from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import os


def setup_tracing(service_name: str):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)
