import requests
from flask import Flask, jsonify

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# OTel セットアップ
provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.route("/")
def index():
    return jsonify({"message": "Hello from OpenTelemetry + Jaeger demo!"})


@app.route("/api/users")
def get_users():
    with tracer.start_as_current_span("fetch-users"):
        users = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        return jsonify(users)


@app.route("/api/order")
def create_order():
    with tracer.start_as_current_span("create-order") as span:
        span.set_attribute("order.item", "sample-item")
        span.set_attribute("order.quantity", 1)
        return jsonify({"status": "order created", "item": "sample-item"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
