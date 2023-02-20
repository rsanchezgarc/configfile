import os
import subprocess
import sys
from typing import List, Optional, Dict
from unittest import TestCase


class TestConfig(TestCase):

    def test_instantiateAbstract(self):
        from configfile.configbase import ConfigBase
        try:
            conf = ConfigBase()
        except TypeError as e:
            self.assertTrue(str(e).startswith("Can't instantiate abstract class"))
            return
        self.fail()

    def test_simpleConfig(self):

        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        self.assertEqual(conf.conf1Str, "caca")

    def test_instantiateSeveralConfs(self):

        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        default_val = conf.conf1Int
        conf.conf1Int = 95
        conf = _MyConfig1()
        self.assertEqual(conf.conf1Int,95)
        conf = _MyConfig1()
        self.assertNotEqual(conf.conf1Int,default_val)

    def test_get(self):
        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        self.assertEqual(conf.conf1Str, conf["conf1Str"])
        try:
            conf["not_valid"]
        except AttributeError:
            return
        self.fail()

    def test_set(self):
        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        conf["conf1Int"] = 99
        self.assertEqual(conf.conf1Int, 99)
        conf.conf1Int = -1
        self.assertEqual(conf.conf1Int, -1)

    def test_get_from_environ(self):
        from tests._configExample import MyConfig1, MyConfig2
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        os.environ[conf.param_to_env_name("conf1Int")] = "10"
        self.assertEqual(conf["conf1Int"], 10)
        class _MyConfig2(MyConfig2): pass
        conf2 = _MyConfig2()
        os.environ[conf2.param_to_env_name("conf2Int")] = "10"
        self.assertEqual(conf2["conf2Int"], 10)


    def test_load_yml(self):
        from tests._configExample import MyConfig2
        class _MyConfig2(MyConfig2): pass
        conf = _MyConfig2(config_file=os.path.join(os.path.dirname(__file__),"data/myconfig2.yaml"))
        # print(conf.all_parameters_dict)
        self.assertEqual(conf["conf2Str"], "test_myconfig2")
        self.assertEqual(conf["conf2List"], [-100, -2])

    def test_update(self):
        from tests._configExample import MyConfig2
        conf = MyConfig2()
        conf.update(dict(conf2Int=-1, conf2List=[-1, -5]))
        self.assertEqual(conf["conf2Int"], -1)
        self.assertEqual(conf["conf2List"], [-1, -5])

    def test_argparse(self):

        from tests._configExample import MyConfig1
        from typing import Optional
        from argparse import ArgumentParser

        class _MyConfig1(MyConfig1):
            def set_parameters(self):
                super().set_parameters()
                self.null_param:Optional[int] = None
        conf = _MyConfig1()
        self.assertEqual(conf.conf1Str, "caca")
        parser = ArgumentParser()
        conf.add_args_to_argparse(parser)
        # parser.print_help()
        pars = parser.parse_args(["--null_param", "3"])
        self.assertEqual(pars.null_param, 3)

        pars = parser.parse_args(["--conf1Int", "32"])
        self.assertEqual(pars.conf1Int, 32)

        class _MyConfig3(MyConfig1):
            def set_parameters(self):
                self.one_list:List[float]=[1.,12.]
                self.null_list:Optional[List[float]]=None

        conf = _MyConfig3()
        parser = ArgumentParser()
        conf.add_args_to_argparse(parser)
        # parser.print_help()
        pars = parser.parse_args(["--one_list", "3", "82"])
        self.assertAlmostEqual(sum(pars.one_list), sum([3, 82]))

        pars = parser.parse_args(["--null_list", "3", "82"])
        self.assertAlmostEqual(sum(pars.null_list), sum([3, 82]))


    def test_inheritance0(self):
        from tests._configExample import MyConfig2
        from configfile import ConfigBase

        conf2 = MyConfig2("MyConfig2")
        print(conf2.conf2Int)
        print(conf2.conf2Str)

        class MyConf3(ConfigBase):
            def set_parameters(self):
                self.conf3Str: str = "3"
                self.conf3Not: Optional[str] = None
                self._add_params_from_other_config(conf2)

        conf3 = MyConf3()
        self.assertTrue(conf3.conf3Str == "3")
        self.assertTrue(conf3.MyConfig2__conf2Str == "tua")

    def test_inheritance1(self):
        from tests._configExample import MyConfig1
        from configfile import ConfigBase

        conf1 = MyConfig1("MyConfig1")

        class MyConfig2(ConfigBase):
            def set_parameters(self):
                self._add_params_from_other_config(conf1)
                self.conf2Int = 2
                self.conf2Str ="tua"

        conf2 = MyConfig2("MyConfig2")

        class MyConf3(ConfigBase):
            def set_parameters(self):
                self.conf3Str: str = "3"
                self._add_params_from_other_config(conf2)

        conf3 = MyConf3()
        self.assertEqual(conf3.conf3Str, "3")
        self.assertEqual(conf3.MyConfig2__conf2Str, "tua")
        self.assertEqual(conf3.MyConfig2__MyConfig1__conf1Str, "caca")
        self.assertEqual(conf3.MyConfig2__conf2Int, 2)

    def test_inheritance2(self):
        from tests._configExample import MyConfig1
        from configfile import ConfigBase

        conf1 = MyConfig1("MyConfig1")

        class MyConfig2(ConfigBase):
            def set_parameters(self):
                self.conf2Int = 2
                self.conf2Str ="tua"

        conf2 = MyConfig2("MyConfig2")

        class MyConf3(ConfigBase):
            def set_parameters(self):
                self._add_params_from_other_config(conf1)
                self.conf3Str: str = "3"
                self._add_params_from_other_config(conf2)

        conf3 = MyConf3()
        # from argparse import ArgumentParser
        # parser = ArgumentParser()
        # conf3.add_args_to_argparse(parser)
        # parser.print_help()
        self.assertEqual(conf3.conf3Str, "3")
        self.assertEqual(conf3.MyConfig2__conf2Str, "tua")
        self.assertEqual(conf3.MyConfig1__conf1Str, "caca")
        self.assertEqual(conf3.MyConfig2__conf2Int, 2)
        self.assertTrue(not hasattr(conf3 , "MyConfig2__MyConfig1__conf1Str"))




    def test_multiprocessing(self):

        from configfile import ConfigBase
        class MyConfig1(ConfigBase):
            def set_parameters(self):
                self.conf1Int = 2
                self.conf1Str ="caca"

        conf = MyConfig1("test_multiprocessing")
        self.assertEqual(conf.conf1Int, 2)
        conf.conf1Int = 10
        self.assertEqual(conf.conf1Int, 10)

        import multiprocessing
        def func():
            assert conf.conf1Int == 10

        p = multiprocessing.Process(target=func)
        p.start()
        p.join()


    def test_multiprocessing2(self):
        from tests._configExample2 import MyConfig1 as confBase
        class MyConfig1(confBase): #TO PREVENT SINGLETON
            pass
        conf = MyConfig1("test_multiprocessing2")
        self.assertEqual(conf.conf1Int, 1)
        conf.conf1Int = 10
        self.assertEqual(conf.conf1Int, 10)

        import multiprocessing
        def func():
            assert conf.conf1Int == 10

        p = multiprocessing.Process(target=func)
        p.start()
        p.join()

    def test_multiprocessing3(self):
        from tests._configExample2 import conf
        self.assertEqual(conf.conf1Int, 1)
        conf.conf1Int = 10
        self.assertEqual(conf.conf1Int, 10)
        try:
            import multiprocessing
            for context in ["fork", "forkserver", "spawn"]:
                print(context)
                p = multiprocessing.get_context(context).Process(target=_func)
                p.start()
                p.join()
                self.assertEqual(p.exitcode, 0)
        finally:
            try:
                del conf
            except:
                pass

    def test_multiprocessing4(self):
        out = 1
        try:
            python = sys.executable
            out = subprocess.check_call([python, "-m", "configfile.tests._exec_example.main"])
        except subprocess.CalledProcessError:
            pass
        self.assertEqual(out, 0)

    def test_multiple_yaml(self):
        from configfile.configbase import ConfigBase
        from tests._configExample import MyConfig2

        class _MyConfig2(MyConfig2): pass

        conf2 = _MyConfig2(config_file=os.path.join(os.path.dirname(__file__), "data/myconfig2.yaml"))

        class MyConfig_yaml(ConfigBase):

            def set_parameters(self):
                self.conf_3_List = ["one", "two"]
                self.conf_3_int = 0
                self._add_params_from_other_config(conf2)

        conf = MyConfig_yaml(config_file=os.path.join(os.path.dirname(__file__), "data/myconfig_3.yaml"))

        self.assertEqual(conf.conf_3_int, 3)
        self.assertEqual(conf.CONFIG__MyConfig2__conf2List, [-100, -2])


    def test_dict_as_attr(self):
        from configfile.configbase import ConfigBase

        class MyConfig(ConfigBase):

            def set_parameters(self):
                self.conf_dict = {"key1":1, "key2":2}

        conf = MyConfig()

        self.assertEqual(conf.conf_dict, {"key1":1, "key2":2})


    def test_dict_as_attr2(self):
        from configfile.configbase import ConfigBase

        class MyConfig(ConfigBase):

            def set_parameters(self):
                self.conf_dict:Optional[Dict[str, int]] = None

        conf = MyConfig()

        self.assertEqual(conf.conf_dict, None)

def _func():
    from tests._configExample2 import conf

    if conf.conf1Int != 10:
        raise RuntimeError()
