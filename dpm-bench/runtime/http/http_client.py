import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from runtime.codec import WireCodec
from runtime.core import NetworkClient, operation_methods


class HttpClient(NetworkClient):
    def __init__(self, interface, base_url, statistics, participant_id, timeout=5.0):
        self.operations = operation_methods(interface)
        self.codec = WireCodec.for_algorithm(interface)
        self.base_url = base_url.rstrip("/")
        self.statistics = statistics
        self.participant_id = participant_id
        self.timeout = timeout

    def call(self):
        return self

    def __getattr__(self, method_name):
        operation_name = self.operations.get(method_name)
        if operation_name is None:
            raise AttributeError(method_name)

        def invoke(*args, **kwargs):
            self.statistics.record_call(self.participant_id, operation_name)
            body = self.codec.encode(
                {
                    "args": list(args),
                    "kwargs": kwargs
                }
            )
            request = Request(
                f"{self.base_url}/{quote(operation_name, safe='')}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urlopen(request, timeout=self.timeout) as response:
                payload = self.codec.decode(json.loads(response.read().decode("utf-8")))
                return payload["result"]

        return invoke
