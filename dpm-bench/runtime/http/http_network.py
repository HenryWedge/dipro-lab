from runtime.core import Network, DistributedAlgorithm
from runtime.http.http_network_statistics import HttpNetworkStatistics
from runtime.http.http_runtime import HttpRuntime


class HttpNetwork(Network):
    def __init__(self, host="0.0.0.0"):
        self.participant_addresses = {}
        self.host = host
        self.statistics = HttpNetworkStatistics(timeout=5.0)
        self.runtimes = {}

    def add_runtime(self, identifier: str, algorithm: DistributedAlgorithm):
        runtime = HttpRuntime(
            algorithm,
            statistics=self.statistics,
            participant_id=identifier,
            host=self.host,
        )
        client = runtime.start(self)
        self.runtimes[identifier] = runtime
        self.participant_addresses[identifier] = client

    def call(self, participant_id):
        return self.participant_addresses[participant_id].call()

    def get_participant_ids(self):
        return list(self.participant_addresses.keys())

    def stop(self):
        for runtime in self.runtimes.values():
            runtime.stop()
