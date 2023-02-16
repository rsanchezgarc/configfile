# configfile
import collections
import os
from abc import abstractmethod
from typing import Optional, get_type_hints

import yaml
from configfile.exceptions import ConfigErrorFromEnv, ConfigErrorParamNotDefined, ConfigErrorParamTypeMismatch
from configfile.utils import AbstractSingleton


class ConfigBase(metaclass=AbstractSingleton):
    NAME = "CONFIG"
    VALID_TYPES_FOR_ENV=[bool, str, int, float]
    PREFIX_ENV_SEP = "___"
    NESTED_SEPARATOR = "__"
    def __init__(self, name:str=None, config_file:Optional[str]=None, environ_vars_overwrite_conf:bool=True):

        if name == None:
            name = ConfigBase.NAME + "_" + type(self).__name__
        self.name = name
        self.environ_vars_overwrite_conf = environ_vars_overwrite_conf

        current_attrib = set(self.__dict__.keys())
        self.set_parameters()
        all_parameters_names = self.__dict__.keys() - current_attrib
        # self.environ_vars_overwrite_conf = environ_vars_overwrite_conf

        #os.environ["MyConfig2___intparam"]



        self.attr_2_type_dict_for_env = {} #TODO: Fill types dict by analysing all newly added parameters
        self.attr_2_type_dict = {} #TODO: Fill types dict by analysing all newly added parameters
        for attr in all_parameters_names:
            newtype = type(self.__dict__[attr])
            self.attr_2_type_dict[attr] = newtype
            if newtype in ConfigBase.VALID_TYPES_FOR_ENV:
                self.attr_2_type_dict_for_env[attr] = newtype

        self.all_parameters_names = all_parameters_names  #Warning:  this variable is used in self.set, so it should be always defined after self.attr_2_type_dict_for_env
        if environ_vars_overwrite_conf:
            for varname in all_parameters_names:
                self.set(varname, self.get(varname))
                # delattr(self, varname)

        if config_file is not None:
            with open(config_file, "r") as f:
                yaml_data = yaml.safe_load(f)
            for attrdict in yaml_data["parameters"]:
                key = list(attrdict.keys())[0]
                val = list(attrdict.values())[0]
                if key not in self.attr_2_type_dict:
                    raise ConfigErrorParamNotDefined(f"Error, {key} parameter from yaml file {config_file} has not been "
                                                     f"previously defined in set_parameters")
                if type(val) != self.attr_2_type_dict[key]:
                    raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter from yaml file {config_file} has "
                                                       f"incompatible type with respect what was defined in "
                                                       f"set_parameters, {type(val),  self.attr_2_type_dict[key]}")
                self.set(key, val)

    def param_to_env_name(self, paramname):
        return self.name + ConfigBase.PREFIX_ENV_SEP + paramname

    def env_to_param_name(self, envname):
        return envname.split(ConfigBase.PREFIX_ENV_SEP)[-1]

    @property
    def all_parameters_dict(self):
        param_dict = {}
        for key in self.all_parameters_names:
            param_dict[key] = self.__dict__[key]
        return param_dict

    @abstractmethod
    def set_parameters(self):
        """
        This method is used to define the config arguments as self.ARGUMENT_NAME=default_value
        Be specially cautious when using floats or integers (1.0 vs 1)
        """
        return NotImplementedError

    #TODO: ensure that only parent process can change config values

    def add_params_from_other_config(self, config):
        selfParamsNames = self.__dict__.get("all_parameters_names", set())
        self.all_parameters_names = selfParamsNames.union(config.all_parameters_dict.keys())
        for k,v in config.all_parameters_dict.items():
            setattr(self, config.name+"_"+k, v)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def get(self, key):

        if self.environ_vars_overwrite_conf:
            envkey = self.param_to_env_name(key)
            if envkey in os.environ:
                try:
                    value = os.environ[envkey]
                    # if type(value) == self.attr_2_type_dict[key]:
                    return self.attr_2_type_dict_for_env[key](value)
                except KeyError:
                    raise ConfigErrorFromEnv(f"Error, {key} cannot be casted. Unknown type")
                except TypeError:
                    raise ConfigErrorFromEnv(f"Error, {os.environ[envkey]} cannot be cast to {self.attr_2_type_dict_for_env[key]}")

        return getattr(self, key)


    def _set_in_env(self, key, value):
        if self.environ_vars_overwrite_conf:
            envkey = self.param_to_env_name(key)
            if envkey in os.environ and type(value) == self.attr_2_type_dict_for_env[key]:
                os.environ[envkey] = str(value)

    def set(self, key, value):
        if key not in self.all_parameters_names:
            raise ConfigErrorParamNotDefined(f"Error, argument {key} was not defined as a valid parameter")
        self._set_in_env(key, value)
        setattr(self, key, value)


    def __getattr__(self, key):
        all_parameters_names = self.__dict__.get("all_parameters_names", {})
        if key in all_parameters_names:
            return self.get(key)
        else:
            raise AttributeError(f"Error, {key} is not a valid config parameter")

    def __setattr__(self, key, value):
        added_attrib = self.__dict__.get("all_parameters_names", {})
        if key in added_attrib:
            self._set_in_env(key, value)
        self.__dict__[key] = value

    def update(self, params_dict:dict):
        for key, val in params_dict.items():
            if key in self.all_parameters_names:
                self.set(key, val)
            else:
                raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter in the dictionary {params_dict} is not difined in the default parameters")

    def add_args_to_argparse(self, parser):

        from configfile.utils import function_local_annotations, allowed_types, allowed_typenames
        annotations = function_local_annotations(self.set_parameters)
        all_params = flatDict(self.all_parameters_dict, sep=self.NESTED_SEPARATOR)
        for k,v in all_params.items():
            if v is None:
                assert k in annotations, f"Error, argument {k} is None, but has no type hint in config"
                type_name = annotations[k]["type"]
                _type = allowed_types[allowed_typenames.index(type_name)]
                nargs = "+" if annotations[k]["isList"] else None

            elif isinstance(v, (list, tuple)):
                nargs="+"
                types = [type(x) for x in v]
                types_names = set()
                for t in types:
                    assert t in allowed_types, f"Error, only _type {allowed_types} are allowed. Got {k,v, t}"
                    types_names.add(t.__name__)
                assert len(types_names) == 1, f"Error, only homogeneous lists are allowed {k,v, t}"
                _type = types[0]
                type_name = types_names.pop()
            else:
                nargs=None
                _type = type(v)
                assert _type in allowed_types, f"Error, only _type {allowed_types} are allowed. Got {k,v, _type}"
                type_name = _type.__name__

            if k in annotations:
                assert type_name == annotations[k]["type"], f"Error, mismatch between type hint and set value " \
                                                            f"{k, type_name == annotations[v]['type']}"

            help = f" {type_name}. Default={v}"
            parser.add_argument(f"--{k.lower()}", type=_type, default=v, nargs=nargs, help=help)
        return parser


    def __str__(self):
        return str(self.all_parameters_dict)

def flatDict(d, parent_key='', sep='__'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)