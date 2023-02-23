# configfile
import collections
import inspect
import json
import multiprocessing
import os
from abc import abstractmethod
from functools import partial
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




class ConfigBase(metaclass=AbstractSingleton):
    PROJECT_NAME = ""
    VALID_TYPES = ALLOWED_TYPES #TODO: Enforce type checking

    def __init__(self, name:str=None, config_file:Optional[str]=None):

        if name == None:
            name = type(self).__name__
        self.name = name

        env_vars = os.environ.copy()
        self._storage = MultiStorage(name=name, fallbackStorageClassName="EnvVarsStorage") #"EnvVarsStorage" is required to overwrite values from envvars


        # self.config_classes_classPrefix = [(type(self), "")] #By default, the main Config has no prefix
        self.config_classname_2_annotations_prefix = {self.name:(get_annotations_from_function(self.set_parameters),"")} #By default, the main Config has no prefix


        self.env_var_prefix = param_to_env_name(self.PROJECT_NAME+self.name, PREFIX_ENV_SEP, "")
        self._adding_params_flag = False # A flag that switches from default setattr to store into _storage
        self.initialize_params()
        self._initialized = True

        if config_file is not None:
            assert self.DEFAULT_YML_ENVVARNAME not in os.environ, "Error, config_file yaml was provided in the builder and as environmental variable"
            self.override_with_yaml(config_file)
        elif  self.DEFAULT_YML_ENVVARNAME in os.environ:
            self.override_with_yaml(os.environ[self.DEFAULT_YML_ENVVARNAME])

        self.override_with_env_vars(env_vars)


    @property
    def all_parameters_dict(self):
        return dict(self._storage.items())

    @property
    def DEFAULT_YML_ENVVARNAME(self):
        return self.PROJECT_NAME+self.name+"_conf.yaml"

    def param_to_env_name(self, k):
        return param_to_env_name(self.PROJECT_NAME+self.name, PREFIX_ENV_SEP, k)

    def initialize_params(self):
        with multiprocessing.Lock():
            self._adding_params_flag = True
            self.set_parameters()
            self._adding_params_flag = False

    def override_with_yaml(self, config_file):
        with open(config_file, "r") as f:
            yaml_data = yaml.safe_load(f)
        for attrdict in yaml_data["parameters"]:
            key = list(attrdict.keys())[0]
            val = list(attrdict.values())[0]
            if key not in self._storage.keys():
                raise ConfigErrorParamNotDefined(f"Error, {key} parameter from yaml file {config_file} has not been "
                                                 f"previously defined in set_parameters")
            #TODO: Do type checking
            # _type = get_annotations_from_value(val)
            # if _type != self.attr_2_type[key]:
            #     raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter from yaml file {config_file} has "
            #                                        f"incompatible type with respect what was defined in "
            #                                        f"set_parameters, {type(val), self.attr_2_type[key]}")
            self._storage.put(key, val)


    def override_with_env_vars(self, env_vars=None):
        if env_vars is None:
            env_vars = os.environ.copy()
        for k,v in env_vars.items():
            if k.startswith(self.env_var_prefix):
                varname = env_to_param_name(k, PREFIX_ENV_SEP)
                if varname not in self._storage.keys():
                    raise ConfigErrorParamNotDefined(f"Error, {k} variable, found as environmental variable has not been previously defined")
                #TODO: check type
                v = load_envvar_to_param(v)
                self._storage.put(varname, v)

    def update(self, params_dict:Dict[str,Any]):
        for key, val in params_dict.items():
            if key in self._storage.keys():
                self._storage.put(key, val)
            else:
                raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter in the dictionary {params_dict} is not difined in the default parameters")

    def add_args_to_argparse(self, parser):

        annotations = self._get_annotations_from_function()
        # all_params = flatDict(self.all_parameters_dict, sep=NESTED_SEPARATOR)
        all_params = self.all_parameters_dict
        for k,v in all_params.items():
            if v is None:
                assert k in annotations, f"Error, argument {k} is None, but has no type hint in config"
                _type = annotations[k]["dtype"]
                type_name = _type.__name__
                if annotations[k]["isDict"]:
                    parser.add_argument("--" + k, help="A dictionary to be provided as json string", action=ParseJsonAction)
                    continue
                assert not annotations[k]["isDict"], "Not implemented yet"
                nargs = "+" if annotations[k]["isList"] else None

            elif isinstance(v, (list, tuple)):
                nargs="+"
                types = [type(x) for x in v]
                types_names = set()
                for t in types:
                    assert t in ALLOWED_TYPES, f"Error, only _type {ALLOWED_TYPES} are allowed. Got {k,v, t}"
                    types_names.add(t.__name__)
                assert len(types_names) == 1, f"Error, only homogeneous lists are allowed {k,v, types_names}"
                _type = types[0]
                type_name = types_names.pop()

            elif isinstance(v, (dict)): # We are using flatten instead of json option
                    parser.add_argument("--" + k, help="A dictionary to be provided as json string",
                                        action=ParseJsonAction)
                    continue
            else:
                nargs=None
                _type = type(v)
                assert _type in ALLOWED_TYPES, f"Error, only _type {ALLOWED_TYPES} are allowed. Got {k,v, _type}"
                type_name = _type.__name__

            if k in annotations:
                assert _type == annotations[k]["dtype"], f"Error, mismatch between type hint and set value " \
                                                            f"{k, _type,  annotations[v]['type']}"

            help = f" {type_name}. Default={v}"
            if _type == bool:
                assert v is not None, "Error, bool arguments need to have associated default value. %s does not" % k
                if v is True:
                    action = "store_false"
                    varname = "NOT_" + k
                else:
                    action = "store_true"
                    varname = k
                help += " Action: " + action + " for variable %s" % k
                parser.add_argument("--" + varname, help=help, action=action, dest=k)
            else:
                parser.add_argument(f"--{k}", type=_type, default=v, nargs=nargs, help=help)
        return parser


    def _add_params_from_other_config(self, config):
        assert isinstance(config, ConfigBase), "Error, config is not of class ConfigBase"
        assert inspect.stack()[1].function == "set_parameters"
        # self.config_classes_classPrefix.append((type(config), config.name+NESTED_SEPARATOR) )
        self.config_classname_2_annotations_prefix[config.name] = (get_annotations_from_function(config.set_parameters),
                                                                   config.name+NESTED_SEPARATOR)
        self._storage.addStorage(config._storage)
        return dict(config.all_parameters_dict.copy())


    def _get_annotations_from_function(self):
        annotated_types= {}
        # for cls in self.__class__.mro():
        # for cls, prefix in self.config_classes_classPrefix:
        for _annot, prefix in self.config_classname_2_annotations_prefix.values():
            _annot = {prefix+k:v for k,v in _annot.items()}
            annotated_types.update(_annot)
        return annotated_types

    @abstractmethod
    def set_parameters(self):
        """
        This method is used to define the config arguments as self.ARGUMENT_NAME=default_value
        Be specially cautious when using floats or integers (1.0 vs 1)
        """
        return NotImplementedError

    def __setattr__(self, key, value):

        if hasattr(self, "_adding_params_flag") and self._adding_params_flag:
            if key == "_adding_params_flag":
                super().__setattr__(key, value)
            else:
                self._storage.put(key, value)
        else:
            if hasattr(self, "_storage") and key in self._storage.keys():
                self._storage.put(key, value)
            else:
                super().__setattr__(key, value)

    def _get_from_storages(self, key):
        try:  # This works because keys in storage are never stored as part of the __dict__
            return self._storage.get(key)
        except KeyError:
            raise ConfigErrorParamNotDefined(f"Error, argument {key} was not defined as a valid parameter")

    def __getattr__(self, key):

        if "_initialized" in self.__dict__ and self._initialized:
            return self._get_from_storages(key)
        else:
            try:
                return self.__dict__[key]
            except KeyError:
                raise AttributeError(f"Error, attribute {key} not found in {self}")

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return self._storage.put(key, value)

    def __str__(self):
        if "_initialized" in self.__dict__ and self._initialized:
            return str(self.all_parameters_dict)
        return super().__str__()

