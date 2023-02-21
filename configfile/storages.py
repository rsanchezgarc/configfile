import json
import os
from abc import abstractmethod

from configfile.constants import PREFIX_ENV_SEP
from configfile.envVarUtils import param_to_env_name


class BaseStorage():

    @abstractmethod
    def put(self, k, v):
        raise NotImplementedError()

    @abstractmethod
    def get(self, k, v):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, k):
        raise NotImplementedError()

    @abstractmethod
    def items(self):
        raise NotImplementedError()

    @abstractmethod
    def keys(self):
        raise NotImplementedError()

class EnvVarsStorage():

    def __init__(self, name, prefix_sep=PREFIX_ENV_SEP):
        self.prefix = name
        self.prefix_sep = prefix_sep
        self._keys = set()

    def param_to_env_name(self, paramname):
        return param_to_env_name(self.prefix, self.prefix_sep, paramname)

    def keys(self):
        return self._keys

    def put(self, k, v):
        self._keys.add(k)
        k = self.param_to_env_name(k)
        os.environ[k] = json.dumps(v)

    def get(self, k):
        k = self.param_to_env_name(k)
        return json.loads(os.environ[k])

    def delete(self, k):
        k = self.param_to_env_name(k)
        del os.environ[k]
        self._keys.remove(k)

    def items(self):
        for k in self._keys:
            yield k, self.get(k)