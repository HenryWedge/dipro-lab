from runtime.core import Network, DistributedAlgorithm
from runtime.local.local_network_statistics import LocalNetworkStatistics
from runtime.local.local_runtime import LocalRuntime
from runtime.local.local_tracer import LocalNetworkTracer


class LocalNetwork(Network):
    def __init__(self):
        self.participant_addresses = {}
        self.statistics = LocalNetworkStatistics()
        self.tracer = LocalNetworkTracer()

    def add_runtime(self, identifier: str, algorithm: DistributedAlgorithm):
        client = LocalRuntime(algorithm).start(self)
        self.participant_addresses[identifier] = client

    def call(self, participant_id):
        target = self.participant_addresses[participant_id].call()
        return LocalNetworkCallProxy(target, participant_id, self.statistics.record_call, self.tracer)

    def get_participant_ids(self):
        return list(self.participant_addresses.keys())

class LocalNetworkCallProxy:
    def __init__(self, target, participant_id, record_call_fn, tracer):
        self.target = target
        self.record_call_fn = record_call_fn
        self.participant_id = participant_id
        self.tracer = tracer

    def __getattr__(self, endpoint_name):
        endpoint = getattr(self.target, endpoint_name)

        def instrumented(*args, **kwargs):
            self.record_call_fn(endpoint_name)
            with self.tracer.span(self.participant_id, endpoint_name, args):
                return endpoint(*args, **kwargs)

        return instrumented


