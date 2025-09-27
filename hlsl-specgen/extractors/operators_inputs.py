import importlib
from .base import Extractor, dedup_by_key

class OperatorsIn(Extractor):
    name = "Operators (local inputs)"
    target_key = "operators"

    def __init__(self, module_path: str = "extractors.inputs.operators_data", attr: str = "OPERATORS"):
        self.module_path = module_path
        self.attr = attr

    def run(self):
        mod = importlib.import_module(self.module_path)
        ops = getattr(mod, self.attr, None)
        if not isinstance(ops, list):
            raise RuntimeError(f"{self.module_path}.{self.attr} not found or not a list")
        # quick schema sanity
        for i, op in enumerate(ops):
            if not all(k in op for k in ("name","precedence","left_to_right","kind")):
                raise RuntimeError(f"operators[{i}] missing required fields")
        return dedup_by_key(ops, key="name")
