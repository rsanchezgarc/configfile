import collections
import functools
import re
from abc import ABCMeta
import inspect
import ast

from configfile.constants import ALLOWED_TYPES, ALLOWED_TYPE_NAMES, VALID_ANNOTATION_LIST_REGEX_PATT


class Singleton(type):
    """
    Metaclass to prevent several instances of the class Config
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def flatDict(d, parent_key='', sep='__'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class AbstractSingleton(ABCMeta):
    """
    Metaclass to prevent several instances of the class Config
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(AbstractSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AnnotationsCollector(ast.NodeVisitor):
    """Collects AnnAssign nodes for 'simple' annotation assignments"""

    def __init__(self):
        self.annotations = {}


    def get_anno(self, anno):
        if hasattr(anno, "slice"):
            assert anno.value.id in ["Optional", "List"], "Error, only Optional[T] or List[T] allowed"
            if anno.value.id == "Optional":
                # return self.get_anno(anno.slice.value) #This is for old versions
                return self.get_anno(anno.slice)
            else:
                # content = anno.slice.value.id #This is for old versions
                content = anno.slice.id
                isList = True
        elif hasattr(anno, "value"):
            content = anno.value.id
            isList = False
        else:
            content = anno.id
            isList = False

        assert content in ALLOWED_TYPE_NAMES, f"Error, only allowed_types {ALLOWED_TYPES}, provided {content}"

        return {"dtype": ALLOWED_TYPES[ALLOWED_TYPE_NAMES.index(content)],
                "isList": isList}

    def visit_AnnAssign(self, node):
        if node.simple:
            self.annotations[node.target.id] = self.get_anno(node.annotation)
        elif node.target.value.id == "self":
            # print(node.target.value.id, node.target.attr, node.annotation.value.id)
            self.annotations[node.target.attr] = self.get_anno(node.annotation)


def get_annotations_from_function(func):
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


def get_annotations_from_value(value): #TODO: Add homogeneus dictionary compability
    if isinstance(value, (list, tuple)):
        isList = True
        types = [type(x) for x in value]
        set_types = set([t.__name__ for t in types])
        assert len(set_types) == 1, "Error only homogeneous lists are allowed"
        assert all(t in ALLOWED_TYPE_NAMES for t in set_types), f"Error not primitive type detected {set_types}"
        content = types.pop()
    else:
        isList = False
        content = type(value)
        assert content.__name__ in ALLOWED_TYPE_NAMES , f"Error not primitive type detected {content}"

    return {"dtype": content, "isList": isList}

@functools.lru_cache
def typeBuilder(dtype, isList, isInputStr=True):
    if not isList:
        return dtype
    else:
        if isInputStr:
            prepro = lambda x: ast.literal_eval(x)
        else:
            prepro = lambda x: x
        return lambda val: [typeBuilder(dtype, isList=False)(x) for x in prepro(val)] if val is not None else None

# def typeName2Builder(typeName, isInputStr=False):
#
#     if typeName in ALLOWED_TYPE_NAMES:
#         return ALLOWED_TYPES[ALLOWED_TYPE_NAMES.index(typeName)]
#     elif typeName.startswith("List") or typeName.startswith("Tuple"):
#         _typename= re.match(VALID_ANNOTATION_LIST_REGEX_PATT, typeName)
#         assert _typename, f"Error, Not valid typeString, {typeName}"
#         _typename = _typename.group(2)
#         if isInputStr:
#             prepro = lambda x: ast.literal_eval(x)
#         else:
#             prepro = lambda x: x
#         return lambda val: [typeName2Builder(_typename)(x) for x in prepro(val)]

# def _test_typeName2Builder():
#     typer = typeName2Builder("List[str]")
#     out = typer([1,2,3])
#     assert  out == ['1', '2', '3']
#     typer = typeName2Builder("List[int]", isInputStr=True)
#     out = typer('[0, 1, 2, 3]')
#     assert out == [0, 1, 2, 3]

# _test_typeName2Builder()

