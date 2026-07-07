import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.langchain import LangChainInstrumentor

_telemetry_initialized = False

def setup_telemetry():
    """Initializes standard OpenTelemetry to send LangChain traces to Phoenix."""
    global _telemetry_initialized
    if _telemetry_initialized:
        return
        
    try:
        resource = Resource(attributes={"project.name": os.getenv("PHOENIX_PROJECT_NAME", "default")})
        tracer_provider = TracerProvider(resource=resource)
        endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006") + "/v1/traces"
        tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(tracer_provider)
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        _telemetry_initialized = True
        print("[Telemetry] Phoenix OpenTelemetry successfully initialized.")
    except Exception as e:
        print(f"[Telemetry] Warning: Failed to initialize telemetry. Tracing may be disabled. Error: {e}")
