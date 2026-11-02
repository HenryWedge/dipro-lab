from abc import ABC, abstractmethod


class DistributedAlgorithm(ABC):
    @property
    def operation_registry(self):
        registry = getattr(self, "_operation_registry", None)
        if registry is None:
            registry = OperationRegistry(self)
            self._operation_registry = registry
        return registry

class NetworkClient(ABC):
    @abstractmethod
    def call(self):
        pass

class Network(ABC):
    @abstractmethod
    def add_runtime(self, identifier: str, algorithm: DistributedAlgorithm):
        pass

    @abstractmethod
    def call(self, participant_id):
        pass

    @abstractmethod
    def get_participant_ids(self):
        pass


class Runtime(ABC):
    @abstractmethod
    def start(self, network: Network) -> NetworkClient:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


def operation():
    def decorate(method):
        method.__distributed_operation__ = method.__name__
        return method

    return decorate

class OperationRegistry:
    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.operations = {}
        self.methods = {}
        self.method_names = {}
        for base in reversed(type(algorithm).__mro__):
            for attribute, declared_method in vars(base).items():
                operation_name = getattr(
                    declared_method, "__distributed_operation__", None
                )
                if operation_name:
                    self.operations[operation_name] = getattr(algorithm, attribute)
                    self.methods[attribute] = operation_name
                    self.method_names[operation_name] = attribute

    def invoke(self, operation_name, *args, **kwargs):
        method = self.operations[operation_name]
        return method(*args, **kwargs)


def operation_methods(algorithm_type):
    methods = {}
    for base in reversed(algorithm_type.__mro__):
        for attribute, declared_method in vars(base).items():
            operation_name = getattr(
                declared_method, "__distributed_operation__", None
            )
            if operation_name:
                methods[attribute] = operation_name
    return methods
