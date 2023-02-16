from abc import ABCMeta
import inspect
import ast


class Singleton(type):
    """
    Metaclass to prevent several instances of the class Config
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AbstractSingleton(ABCMeta):
    """
    Metaclass to prevent several instances of the class Config
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(AbstractSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


allowed_types = (int, str, bool, float) #, type(None))
allowed_typenames = [x.__name__ for x in allowed_types]


class AnnotationsCollector(ast.NodeVisitor):
    """Collects AnnAssign nodes for 'simple' annotation assignments"""

    def __init__(self):
        self.annotations = {}

    # def get_anno(self, anno):
    #     if hasattr(anno, "slice"):
    #         content = anno.slice.value.id
    #         assert content in allowed_typenames, f"Error, only allowed_types {allowed_types}, provided {content}"
    #         assert anno.value.id in ["Optional", "List"], "Error, only Optional[T] or List[T] allowed"
    #         if anno.value.id == "Optional":
    #             isList = False
    #         else:
    #             isList = True
    #     else:
    #         content = anno.value.id
    #         isList = False
    #     return {"type": content, "isList": isList}

    def get_anno(self, anno):
        if hasattr(anno, "slice"):
            assert anno.value.id in ["Optional", "List"], "Error, only Optional[T] or List[T] allowed"
            if anno.value.id == "Optional":
                return self.get_anno(anno.slice.value)
                # isList = False
            else:
                content = anno.slice.value.id
                isList = True
        elif hasattr(anno, "value"):
            content = anno.value.id
            isList = False
        else:
            content = anno.id
            isList = False

        assert content in allowed_typenames, f"Error, only allowed_types {allowed_types}, provided {content}"

        return {"type": content, "isList": isList}

    def visit_AnnAssign(self, node):
        if node.simple:
            self.annotations[node.target.id] = self.get_anno(node.annotation)
        elif node.target.value.id == "self":
            self.annotations[node.target.attr] = self.get_anno(node.annotation)


def function_local_annotations(func):
    """Return a mapping of name to string annotations for function locals

    Python does not retain PEP 526 "variable: annotation" variable annotations
    within a function body, as local variables do not have a lifetime beyond
    the local namespace. This function extracts the mapping from functions that
    have source code available.

    """
    source = inspect.getsource(func)
    sourceLines = source.split("\n")
    n_spaces = len(sourceLines[0]) - len(sourceLines[0].lstrip())
    sourceLines = [x[n_spaces:] for x in sourceLines]
    source = "\n".join(sourceLines)
    mod = ast.parse(source)
    assert mod.body and isinstance(mod.body[0], (ast.FunctionDef, ast.AsyncFunctionDef))
    collector = AnnotationsCollector()
    collector.visit(mod.body[0])

    return collector.annotations
