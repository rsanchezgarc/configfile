# configfile

import os
from abc import abstractmethod
from typing import Optional

import yaml
from configfile.exceptions import ConfigErrorFromEnv, ConfigErrorParamNotDefined, ConfigErrorParamTypeMismatch
from configfile.utils import AbstractSingleton


class ConfigBase(metaclass=AbstractSingleton):
    NAME = "CONFIG"
    VALID_TYPES_FOR_ENV=[bool, str, int, float]
    PREFIX_ENV_SEP = "___"
    def __init__(self, name:str=None, config_file:Optional[str]=None, environ_vars_overwrite_conf:bool=True):

        if name == None:
            name = ConfigBase.NAME
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

        if environ_vars_overwrite_conf:
            for varname in all_parameters_names:
                delattr(self, varname)

        self.all_parameters_names = all_parameters_names  #Warning:  this variable is used in self.set, so it should be always defined after self.attr_2_type_dict_for_env
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



