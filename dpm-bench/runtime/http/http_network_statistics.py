from urllib.request import urlopen
from threading import Lock

class HttpNetworkStatistics:
    def __init__(self, timeout=5.0):
        self.recorder = MetricsRecorder()
        self.client = MetricsClient(timeout=timeout)
        self.endpoint = None

    def set_endpoint(self, base_url):
        if self.endpoint is None:
            self.endpoint = f"{base_url.rstrip('/')}/metrics"

    def record_call(self, participant_id, operation):
        self.recorder.increment(
            "http_network_rpc_requests_total",
            labels={"participant_id": participant_id, "operation": operation},
        )

    def results(self):
        if self.endpoint is None:
            raise RuntimeError("No HTTP runtime has been started")
        return self.client.scrape(self.endpoint)


class MetricsRecorder:
    """Small Prometheus text-format recorder for counters and gauges."""

    def __init__(self, labels=None):
        self.labels = dict(labels or {})
        self._counters = {}
        self._gauges = {}
        self._lock = Lock()

    def increment(self, name, amount=1, labels=None):
        key = (name, self._label_key(labels))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + amount

    def set_gauge(self, name, value, labels=None):
        key = (name, self._label_key(labels))
        with self._lock:
            self._gauges[key] = value

    def reset(self):
        with self._lock:
            self._counters.clear()
            self._gauges.clear()

    def snapshot(self):
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

    def reset(self):
        with self._lock:
            self._counters.clear()
            self._gauges.clear()

    def render(self):
        snapshot = self.snapshot()
        samples = {}
        for metric_type in ("counters", "gauges"):
            for (name, labels), value in snapshot[metric_type].items():
                samples.setdefault(name, []).append((labels, value))

        lines = []
        for name in sorted(samples):
            metric_type = "counter" if name.endswith("_total") else "gauge"
            lines.append(f"# TYPE {name} {metric_type}")
            for labels, value in sorted(samples[name], key=lambda item: item[0]):
                merged_labels = {**self.labels, **dict(labels)}
                label_text = ""
                if merged_labels:
                    label_text = "{" + ",".join(
                        f'{key}="{self._escape_label(value)}"'
                        for key, value in sorted(merged_labels.items())
                    ) + "}"
                lines.append(f"{name}{label_text} {value}")
        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _label_key(labels):
        return tuple(sorted((str(key), str(value)) for key, value in (labels or {}).items()))


    def _escape_label(self, value):
        return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


    def metric_name(self, value):
        """Normalize arbitrary operation identifiers for a Prometheus label value."""
        return str(value)

class MetricsClient:
    """Fetch a Prometheus text exposition from a metrics endpoint."""

    def __init__(self, timeout=5.0):
        self.timeout = timeout

    def scrape(self, endpoint):
        with urlopen(endpoint, timeout=self.timeout) as response:
            return response.read().decode("utf-8")
