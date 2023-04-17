import copy
import json
import os
import uuid
import warnings
from abc import abstractmethod
from typing import Dict, Optional, List, Literal

from configfile.constants import PREFIX_ENV_SEP, NESTED_SEPARATOR, DEFAULT_SIMPLE_STORAGENAME
from configfile.envVarUtils import param_to_env_name, env_to_param_name


class BaseStorage(): #TODO: add code to prevent instantiating several storages with the same name

    def __init__(self, name):
        self._name = name

    @property
    @abstractmethod
    def name(self):
        return self._name

    @abstractmethod
    def put(self, k, v):
        raise NotImplementedError()

    @abstractmethod
    def get(self, k):
        raise NotImplementedError()

    @abstractmethod
    def __contains__(self, k):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, k):
        raise NotImplementedError()

    @abstractmethod
    def items(self):
        raise NotImplementedError()

    def keys(self):
        for k,v in self.items():
            yield k

    def values(self):
        for k,v in self.items():
            yield v

    def dict(self):
        return dict(self.items())

    def __str__(self):
        return str(dict(self.items()))

class SimpleStorage(BaseStorage):
    pass

class EnvVarsStorage(SimpleStorage):

    def __init__(self, name, envNamePrefix=None, prefix_sep=PREFIX_ENV_SEP):

        super().__init__(name)
        super().__init__(name)
        self.envNamePrefix = name if envNamePrefix is None else envNamePrefix
        self.prefix_sep = prefix_sep

    def param_to_env_name(self, paramname):
        return param_to_env_name(self.envNamePrefix, self.prefix_sep, paramname)

    def env_to_param_name(self,envparamname):
        return env_to_param_name(envparamname, self.prefix_sep)

    def keys(self):
        for k,v in self.items():
            yield k

    def put(self, k, v):
        k = self.param_to_env_name(k)
        os.environ[k] = json.dumps(v)

    def get(self, k):
        k = self.param_to_env_name(k)
        return json.loads(os.environ[k])

    def __contains__(self, k):
        k = self.param_to_env_name(k)
        return k in os.environ

    def delete(self, k):
        k = self.param_to_env_name(k)
        del os.environ[k]

    def items(self):
        for k in os.environ.keys():
            if k.startswith(self.envNamePrefix):
                k = self.env_to_param_name(k)
                yield k, self.get(k)

    def __str__(self):
        return self.name + ":" + str(dict(self.items()))

AVAILABLE_SIMPLE_STORAGES={"EnvVarsStorage":EnvVarsStorage}


class MultiStorage(BaseStorage):
    def __init__(self, name:str,
                 fallbackStorageClassName:str= DEFAULT_SIMPLE_STORAGENAME, fallbackStorageKwargs={},
                 extraStorages:Optional[List[BaseStorage]]=None):

        super().__init__(name)

        self.fallbackStorage = AVAILABLE_SIMPLE_STORAGES[fallbackStorageClassName](name=name, **fallbackStorageKwargs)

        self.storages = {}
        if extraStorages:
            for storage in extraStorages:
                self.addStorage(storage)

    @classmethod
    def _storage2MultiVarname(cls, varname, storage):
        return storage.name + NESTED_SEPARATOR + varname

    @classmethod
    def _multi2StorageVarname(cls, varname):

        *storages, name = varname.split(NESTED_SEPARATOR)
        return storages, name

    def addStorage(self, storage):
        #TODO: assert recursevely that the same config object is not present twice or more
        self.storages[storage.name] = storage

    def removeStorage(self, storageName):
        del self.storages[storageName]

    @property
    def name(self):
        return self._name

    def recursive_traversal(self, storage):

        if not isinstance(storage, MultiStorage):
            return [("", storage)]
        else:
            storages = [(storage.name+NESTED_SEPARATOR, storage.fallbackStorage)]
            for nestedStorage in storage.storages.values():
                newLevelStorages = self.recursive_traversal(nestedStorage)
                newLevelStorages = [(storage.name+NESTED_SEPARATOR+n, s) for n,s in newLevelStorages]
                storages += newLevelStorages
            return storages

    def keys(self):
        for k,v in self.items():
            yield k

    def _match_storage_by_varname(self, key):

        storageNames, storageKey = self._multi2StorageVarname(key)
        storage = self._getStorage(storageNames)
        # raise AttributeError(f"Error, attribute {k} was not found in any storage")
        return storage, storageKey

    def _getStorage(self, storageNames:List[str]):

        storageNames = list(reversed((storageNames)))
        currentStorage = self
        while storageNames:
            storName = storageNames.pop()
            currentStorage = currentStorage.storages[storName]

        if currentStorage == self:
            currentStorage = self.fallbackStorage

        return currentStorage

    def put(self, k, v):
        storage, storageKey = self._match_storage_by_varname(k)
        storage.put(storageKey, v)

    def get(self, k):
        storage, storageKey = self._match_storage_by_varname(k)
        return storage.get(storageKey)

    def __contains__(self, k):
        return k in self.keys()

    def delete(self, k):
        storage, storageKey = self._match_storage_by_varname(k)
        storage.delete(storageKey)

    def _iter_prefix_storage(self):
        yield "", self.fallbackStorage
        for primaryStorage in self.storages.values():
            allStorages = self.recursive_traversal(primaryStorage)
            for prefix, storage in allStorages:
                if not isinstance(storage, MultiStorage):
                    yield prefix, storage

    def items(self):
        for prefix, storage in self._iter_prefix_storage():
            if not isinstance(storage, MultiStorage):
                for storageKey, v in storage.items():
                    v = storage.get(storageKey)
                    key = prefix + storageKey #self._storage2MultiVarname(storageKey, storage)
                    yield key, v

    def __str__(self):
        rep = super().__str__()
        if hasattr(self, "_name"):
            rep = self.name + ":" + rep
        return rep