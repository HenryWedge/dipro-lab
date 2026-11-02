class LocalNetworkStatistics:
    def __init__(self):
        self.endpoint_calls = {}

    def record_call(self, method_name):
        if method_name in self.endpoint_calls:
            self.endpoint_calls[method_name] += 1
        else:
            self.endpoint_calls[method_name] = 1

    def results(self):
        return self.endpoint_calls
