import argparse
import collections
import functools
import json
import re
from abc import ABCMeta
import inspect
import ast

from configfile.constants import ALLOWED_TYPES, ALLOWED_TYPE_NAMES, VALID_ANNOTATION_LIST_REGEX_PATT

def flatDict(d, parent_key='', sep='__'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def longestSubstr(data):
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                    substr = data[0][i:i+j]
    return substr

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


class AnnotationsCollector(ast.NodeVisitor):
    """Collects AnnAssign nodes for 'simple' annotation assignments"""

    def __init__(self):
        self.annotations = {}

        self.variables = set()
        self.attributes = set()

    def visit_FunctionDef(self, node):
        for arg in node.args.args:
            if arg.arg != 'self':
                self.variables.add(arg.arg)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            if isinstance(node.targets[0].ctx, ast.Store):
                if node.targets[0].id == 'self':
                    if isinstance(node.value, (ast.Name, ast.Attribute)):
                        self.attributes.add(node.targets[0].id)
                else:
                    self.variables.add(node.targets[0].id)

        elif isinstance(node.targets[0], ast.Attribute):
            if isinstance(node.targets[0].value, ast.Name) and node.targets[0].value.id == 'self':
                self.attributes.add(node.targets[0].attr)


    def get_anno(self, anno):
        isDict = False
        if hasattr(anno, "slice"):
            if anno.value.id in ["Optional", "List", "Dict"]:
                if anno.value.id == "Optional":
                    # return self.get_anno(anno.slice.value) #This is for old versions
                    return self.get_anno(anno.slice)
                else:
                    if anno.value.id == "Dict":
                        assert anno.slice.elts[0].id == "str", "Error, only Dict[str,T] allowed"
                        content = anno.slice.elts[1].id
                        isList = False
                        isDict = True

                    else:
                        content = anno.slice.id
                        # content = anno.slice.value.id #This is for old versions

                        isList = True

            else:
               raise ValueError("Error, only Optional[T] or List[T] or Dict[str,T] allowed")

        elif hasattr(anno, "value"):
            content = anno.value.id
            isList = False
        else:
            content = anno.id
            isList = False

        assert content in ALLOWED_TYPE_NAMES, f"Error, only allowed_types {ALLOWED_TYPES}, provided {content}"

        return {"dtype": ALLOWED_TYPES[ALLOWED_TYPE_NAMES.index(content)],
                "isList": isList, "isDict":isDict}

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
    annota = collector.annotations
    for k in collector.attributes:
        if k not in annota:
            annota[k]=None
    return annota


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



class ParseJsonAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            setattr(namespace, self.dest, json.loads(values))
        except ValueError as e:
            raise argparse.ArgumentError(self, f"Invalid JSON string: {e}")

