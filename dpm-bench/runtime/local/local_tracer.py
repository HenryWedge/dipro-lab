from _contextvars import ContextVar
from contextlib import contextmanager


class LocalNetworkTracer:
    def __init__(self):
        self.roots = []
        self._active_node = ContextVar("network_call", default=None)

    @contextmanager
    def span(self, participant_id, method_name, args):
        node = {
            "participant_id": participant_id,
            "method": method_name,
            "children": [],
            "args": args
        }
        parent = self._active_node.get()
        if parent is None:
            self.roots.append(node)
        else:
            parent["children"].append(node)
        token = self._active_node.set(node)
        try:
            yield
        finally:
            self._active_node.reset(token)

    def results(self):
        return CallTree(self.roots)

    def reset(self):
        self.roots = []



class CallTree:
    def __init__(self, roots):
        self.roots = roots

    def __str__(self) -> str:
        return "\n".join(
            self._render(root, is_root=True)
            for root in self.roots
        )

    def _render(self, node, prefix="", is_last=True, is_root=False):
        connector = "" if is_root else ("└── " if is_last else "├── ")
        line = f"{prefix}{connector}{node['method']}({node['args']}) [{node['participant_id']}]"
        child_prefix = prefix
        if not is_root:
            child_prefix += "    " if is_last else "│   "

        child_lines = [
            self._render(child, child_prefix, index == len(node["children"]) - 1)
            for index, child in enumerate(node["children"])
        ]
        return "\n".join([line, *child_lines])
