import copy
import os
import subprocess
import sys
from typing import List, Optional, Dict
from unittest import TestCase

from configfile.exceptions import ConfigErrorParamNotDefined
from configfile.storages import EnvVarsStorage, MultiStorage


class TestSotrages(TestCase):

    def test_envStorage0(self):
        storage0 = EnvVarsStorage(name="envStorage00")
        storage0.put("kk", "tua")
        self.assertEqual(storage0.get("kk"), "tua")


    def test_multiStorageSimple0(self):

        multiStorage = MultiStorage("multiStorageSimple0")
        multiStorage.put("intVar", 1)
        self.assertEqual(multiStorage.get("intVar"), 1)

    def test_multiStorage0(self):
        storage0 = EnvVarsStorage(name="envStoragem0")
        storage0.put("kk", "tua")
        multiStorage = MultiStorage("mainStoragem0")
        multiStorage.addStorage(storage0)
        new_name = MultiStorage._storage2MultiVarname("kk", storage0)
        self.assertEqual(multiStorage.get(new_name), "tua")
        # print(multiStorage.keys())
        # print(list(multiStorage.items()))

    def test_multiStorage1(self):
        storage0 = EnvVarsStorage(name="envStorage01")
        multiStorage = MultiStorage("mainStorage01")
        multiStorage.addStorage(storage0)
        multiStorageVarname = MultiStorage._storage2MultiVarname("kk", storage0)
        multiStorage.put(multiStorageVarname, "tua")
        # print(list(multiStorage.items()))
        self.assertEqual(multiStorage.get(multiStorageVarname), "tua")
        self.assertEqual(storage0.get("kk"), "tua")
        # print(list(multiStorage.items()))
        # print(list(storage0.items()))
        self.assertEqual(sorted(storage0.values()), sorted(multiStorage.values()))

    def test_multiStorage2(self):

        storage0 = EnvVarsStorage(name="envStorage02")
        storage1 = EnvVarsStorage(name="envStorage12")
        storage1.put("stor1", 2)

        multiStorage = MultiStorage("mainStorage02")
        multiStorage.addStorage(storage1)
        self.assertEqual(multiStorage.get(MultiStorage._storage2MultiVarname("stor1", storage1)), 2)
        multiStorage.addStorage(storage0)

        storageVarname = MultiStorage._storage2MultiVarname("kk", storage0)
        multiStorage.put(storageVarname, "tua")
        self.assertEqual(multiStorage.get(storageVarname), "tua")

        storageVarname = MultiStorage._storage2MultiVarname("kk", storage0)
        multiStorage.put(storageVarname, "tua")
        self.assertEqual(multiStorage.get(storageVarname), "tua")
        self.assertEqual(storage0.get("kk"), "tua")


    def test_multiStorage3(self):

        storage0 = EnvVarsStorage(name="env3_0")
        storage1 = EnvVarsStorage(name="env3_1")
        storage1.put("int31", 11)

        multiStorage0 = MultiStorage("main3_0")
        multiStorage0.addStorage(storage0)

        multiStorage0.addStorage(storage1)

        storage1.put("int11", 1)
        storage2 = EnvVarsStorage(name="env3_2")
        multiStorage1 = MultiStorage("main3_1")
        multiStorage1.addStorage(multiStorage0)

        storageVarname = MultiStorage._storage2MultiVarname(MultiStorage._storage2MultiVarname("int31", storage1),multiStorage0)
        self.assertEqual(multiStorage1.get(storageVarname), 11)

        multiStorage1.put("mainInt", 1)
        self.assertEqual(multiStorage1.get("mainInt"), 1)


        multiStorage1.addStorage(storage2)
        storageVarname = MultiStorage._storage2MultiVarname("strHola", storage2)
        multiStorage1.put(storageVarname, "Hola")
        self.assertEqual(multiStorage1.get(storageVarname), "Hola")
        self.assertEqual(storage2.get("strHola"), "Hola")


    def test_multiStorage4(self):


        multiStorage0 = MultiStorage("main4_0")
        multiStorage1 = MultiStorage("main4_1")
        multiStorage2 = MultiStorage("main4_2")
        multiStorage2.addStorage(multiStorage1)
        multiStorage1.addStorage(multiStorage0)
        multiStorage0.put("int0", 0)
        multiStorage1.put("int1", 1)
        multiStorage0.put("int2", 2)

        self.assertEqual(multiStorage0.get("int0"), 0)
        storageVarname = MultiStorage._storage2MultiVarname("int0", multiStorage0)
        self.assertEqual(multiStorage1.get(storageVarname), 0)
        storageVarname = MultiStorage._storage2MultiVarname(
            MultiStorage._storage2MultiVarname("int0", multiStorage0), multiStorage1)
        self.assertEqual(multiStorage2.get(storageVarname), 0)

        for fullname, v in multiStorage2.items():
            self.assertEqual(multiStorage2.get(fullname), v)