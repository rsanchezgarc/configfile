# configfile
import collections
import inspect
import json
import os
from abc import abstractmethod
from typing import Optional, Dict, Any, List
from configfile.utils import get_annotations_from_function, get_annotations_from_value, typeBuilder
from configfile.constants import ALLOWED_TYPES, ALLOWED_TYPE_NAMES

import yaml
from configfile.exceptions import ConfigErrorFromEnv, ConfigErrorParamNotDefined, ConfigErrorParamTypeMismatch
from configfile.utils import AbstractSingleton


class ConfigBase(metaclass=AbstractSingleton):
    NAME = "CONFIG"

    VALID_TYPES= ALLOWED_TYPES
    PREFIX_ENV_SEP = "___" #Access it only with ConfigBase.PREFIX_ENV_SEP
    NESTED_SEPARATOR = "__" #Access it only with ConfigBase.NESTED_SEPARATOR

    def __init__(self, name:str=None, config_file:Optional[str]=None, environ_vars_overwrite_conf:bool=True):

        if name == None:
            name = ConfigBase.NAME + "_" + type(self).__name__
        self.name = name
        self.environ_vars_overwrite_conf = environ_vars_overwrite_conf
        self.config_classes = [(type(self), "")] #List of duples, first elem, config class, second, str prefix for variables
        current_attrib = set(self.__dict__.keys())
        self.set_parameters()
        all_parameters_names = self.__dict__.keys() - current_attrib

        self.attr_2_typeBuilder = None
        self.attr_2_type = None
        self.init_attr_2_type(all_parameters_names=all_parameters_names)

        self.all_parameters_names = all_parameters_names  #Warning:  this variable is used in self.set, so it should be always defined after self.attr_2_typeBuilder
        if environ_vars_overwrite_conf:
            for varname in all_parameters_names:
                self.set(varname, self.get(varname))
                # delattr(self, varname)

        if config_file is not None:
            self._setYaml(config_file)

    def _setYaml(self, config_file):
        with open(config_file, "r") as f:
            yaml_data = yaml.safe_load(f)
        for attrdict in yaml_data["parameters"]:
            key = list(attrdict.keys())[0]
            val = list(attrdict.values())[0]
            if key not in self.attr_2_type:
                raise ConfigErrorParamNotDefined(f"Error, {key} parameter from yaml file {config_file} has not been "
                                                 f"previously defined in set_parameters")
            _type = get_annotations_from_value(val)
            if _type != self.attr_2_type[key]:
                raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter from yaml file {config_file} has "
                                                   f"incompatible type with respect what was defined in "
                                                   f"set_parameters, {type(val), self.attr_2_type[key]}")
            self.set(key, val)

    def param_to_env_name(self, paramname):
        return self.name + ConfigBase.PREFIX_ENV_SEP + paramname

    def env_to_param_name(self, envname):
        return envname.split(ConfigBase.PREFIX_ENV_SEP)[-1]

    def _get_annotations_from_function(self):
        annotated_types= {}
        # for cls in self.__class__.mro():
        for cls, prefix in self.config_classes:
            if hasattr(cls, "set_parameters"):
                _annot = get_annotations_from_function(cls.set_parameters)
                _annot = {prefix+k:v for k,v in _annot.items() }
                annotated_types.update(_annot)
        return annotated_types

    def init_attr_2_type(self, all_parameters_names=None):

        if self.attr_2_typeBuilder is not None and self.attr_2_type is not None:
            return
        if all_parameters_names is None:
            all_parameters_names = self.all_parameters_names
        self.attr_2_typeBuilder = {} #TODO: Fill types dict by analysing all newly added parameters
        self.attr_2_type = {} #TODO: Fill types dict by analysing all newly added parameters

        annotated_types= self._get_annotations_from_function()
        inferred_types = {attr:get_annotations_from_value(self.get(attr, environ_vars_overwrite_conf=False))
                          for attr in all_parameters_names}

        for k, v in inferred_types.items():
            #TODO: if v is Nonetype -> read from annotated
            if v["dtype"] == type(None):
                assert k in annotated_types, "Error, if None provided as default value, type hint is required. {k, v, annotated_types[k]}"
                v = annotated_types[k]
            if k in annotated_types:
                assert v == annotated_types[k], f"Error, provided type and type hint mismatch. {k, v, annotated_types[k]}"
            self.attr_2_type[k] = v
            self.attr_2_typeBuilder[k] = typeBuilder(**v, isInputStr=False)


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

    def _add_params_from_other_config(self, config, prepend_config_name=True):
        self.config_classes.append((type(config), config.name+self.NESTED_SEPARATOR if prepend_config_name else "") )
        assert  inspect.stack()[1].function == "set_parameters"
        for k,v in config.all_parameters_dict.items():
            if prepend_config_name:
                newname = config.name+self.NESTED_SEPARATOR+k
            else:
                newname = k
            setattr(self, newname, v)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def get(self, key, environ_vars_overwrite_conf=None):

        environ_vars_overwrite_conf = self.environ_vars_overwrite_conf if environ_vars_overwrite_conf is None else False
        if environ_vars_overwrite_conf:
            envkey = self.param_to_env_name(key)
            if envkey in os.environ:
                try:
                    value = json.loads(os.environ[envkey])
                    return self.attr_2_typeBuilder[key](value)
                except KeyError:
                    raise ConfigErrorFromEnv(f"Error, {key} cannot be casted. Unknown type")
                except TypeError:
                    raise ConfigErrorFromEnv(f"Error, {os.environ[envkey]} cannot be cast to {self.attr_2_type[key]}")

        return getattr(self, key)


    def _set_in_env(self, key, value):
        if self.environ_vars_overwrite_conf:
            envkey = self.param_to_env_name(key)
            if get_annotations_from_value(value) == self.attr_2_type[key] or value is None:
                # os.environ[envkey] = str(value)
                os.environ[envkey] = json.dumps(value)
            else:
                raise ValueError(f"Key {key} cannot be stored as environmental variable, type {type(value)}")
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

    def update(self, params_dict:Dict[str,Any]):
        for key, val in params_dict.items():
            if key in self.all_parameters_names:
                self.set(key, val)
            else:
                raise ConfigErrorParamTypeMismatch(f"Error, {key} parameter in the dictionary {params_dict} is not difined in the default parameters")

    def add_args_to_argparse(self, parser):

        annotations = self._get_annotations_from_function()
        all_params = flatDict(self.all_parameters_dict, sep=self.NESTED_SEPARATOR)
        for k,v in all_params.items():
            if v is None:
                assert k in annotations, f"Error, argument {k} is None, but has no type hint in config"
                _type = annotations[k]["dtype"]
                type_name = _type.__name__
                nargs = "+" if annotations[k]["isList"] else None

            elif isinstance(v, (list, tuple)):
                nargs="+"
                types = [type(x) for x in v]
                types_names = set()
                for t in types:
                    assert t in ALLOWED_TYPES, f"Error, only _type {ALLOWED_TYPES} are allowed. Got {k,v, t}"
                    types_names.add(t.__name__)
                assert len(types_names) == 1, f"Error, only homogeneous lists are allowed {k,v, t}"
                _type = types[0]
                type_name = types_names.pop()
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


    def __str__(self):
        return str(self.all_parameters_dict)

    # def remove_env_vars(self):
    #     for key in self.__dict__.get("all_parameters_names", {}):
    #         envkey = self.param_to_env_name(key)
    #         if envkey in os.environ:
    #             del os.environ[envkey]
    #
    # def __del__(self):
    #     self.remove_env_vars()

def flatDict(d, parent_key='', sep='__'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.abc.MutableMapping):
            items.extend(flatDict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
