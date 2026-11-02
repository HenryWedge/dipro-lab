import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from runtime.core import Runtime, Network, NetworkClient, OperationRegistry
from runtime.http.http_client import HttpClient


class HttpRuntime(Runtime):
    def __init__(
        self,
        participant,
        statistics,
        participant_id,
        host="0.0.0.0",
    ):
        self.server = None
        self.participant = participant
        self.interface = type(participant)
        self.statistics = statistics
        self.participant_id = participant_id
        self.host = host
        self.port = 0

    def start(self, network: Network) -> NetworkClient:
        self.participant.set_network(network)
        codec = WireCodec.for_algorithm(self.interface)
        registry = OperationRegistry(self.participant)
        self.server = ThreadingHTTPServer(
            (self.host, self.port),
            partial(
                RpcHandler,
                registry=registry,
                codec=codec,
                metrics_recorder=self.statistics.recorder,
            ),
        )
        self.thread = Thread(
            target=self.server.serve_forever,
            daemon=True
        )
        self.thread.start()
        bound_host, bound_port = self.server.server_address[:2]
        base_url = f"http://{bound_host}:{bound_port}"
        self.statistics.set_endpoint(base_url)
        return HttpClient(
            interface=self.interface,
            base_url=base_url,
            statistics=self.statistics,
            participant_id=self.participant_id,
        )

class RpcHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, registry, codec, metrics_recorder):
        self.registry = registry
        self.codec = codec
        self.metrics_recorder = metrics_recorder
        super().__init__(request, client_address, server)

    def do_GET(self):
        if urlsplit(self.path).path != "/metrics":
            self.send_error(404)
            return

        body = self.metrics_recorder.render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        operation_name = urlsplit(self.path).path[1:]
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.codec.decode(json.loads(self.rfile.read(length).decode("utf-8")))
            result = self.registry.invoke(operation_name, *payload["args"], **payload["kwargs"])
        except Exception as error:
            self._respond(500, {"error": str(error)})
        else:
            self._respond(200, {"result": result})

    def _respond(self, status, payload):
        body = json.dumps(self.codec.encode(payload)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
