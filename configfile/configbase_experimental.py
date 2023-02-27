# configfile
import collections
import inspect
import json
import multiprocessing
import os
from abc import abstractmethod
from typing import Optional, Dict, Any, List

from configfile.envVarUtils import param_to_env_name, env_to_param_name, serialize_param_to_envvar, \
    load_envvar_to_param, load_envvar
from configfile.storages import EnvVarsStorage, MultiStorage
from configfile.utils import get_annotations_from_function, get_annotations_from_value, typeBuilder, flatDict, \
    ParseJsonAction
from configfile.constants import ALLOWED_TYPES, ALLOWED_TYPE_NAMES, PREFIX_ENV_SEP, NESTED_SEPARATOR

import yaml
from configfile.exceptions import ConfigErrorFromEnv, ConfigErrorParamNotDefined, ConfigErrorParamTypeMismatch
from configfile.utils import AbstractSingleton


class ConfigBaseDict(metaclass=AbstractSingleton):
    PROJECT_NAME = ""
    VALID_TYPES = ALLOWED_TYPES  # TODO: Enforce type checking

    def __init__(self, name: str = None, config_file: Optional[str] = None):

        if name == None:
            name = type(self).__name__
        self._name = name
        self._config_vars = {} #TODO: Replace it by sqlitedict or any other dict-like storage


    def __setattr__(self, key, value):
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
            #TODO: FLATTEN AND UNFLATTEN KEYS
            self._config_vars[key] = value

    def __getattr__(self, key):
        if key.startswith("_"):
            return self.__dict__[key]
        else:
            #TODO: FLATTEN AND UNFLATTEN KEYS
            try:
                val = self._config_vars[key]
                return val
            except KeyError:
                raise AttributeError(f"Error, config object does not contain config paramenter {key}")

if __name__ == "__main__":
    class MyConf(ConfigBaseDict):
        pass

    conf = MyConf("MyConf")
    conf.CONF_KK = 1
    conf._kk = 2
    print(conf.CONF_KK)
    print()