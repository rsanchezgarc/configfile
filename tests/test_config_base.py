import os
from typing import List
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
        self.assertEqual(conf.caca, "tua")

    def test_instantiateSeveralConfs(self):

        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        default_val = conf.param1
        conf.param1 = 95
        conf = _MyConfig1()
        self.assertEqual(conf.param1,95)
        conf = _MyConfig1()
        self.assertNotEqual(conf.param1,default_val)

    def test_get(self):
        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        self.assertEqual(conf.param1, conf["param1"])
        try:
            conf["not_valid"]
        except AttributeError:
            return
        self.fail()

    def test_set(self):
        from tests._configExample import MyConfig1
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        conf["param1"] = 99
        self.assertEqual(conf.param1, 99)
        conf.param1 = -1
        self.assertEqual(conf.param1, -1)

    def test_get_from_environ(self):
        from tests._configExample import MyConfig1, MyConfig2
        class _MyConfig1(MyConfig1): pass
        conf = _MyConfig1()
        os.environ[conf.param_to_env_name("param1")] = "10"
        self.assertEqual(conf["param1"], "10")
        class _MyConfig2(MyConfig2): pass
        conf = _MyConfig2()
        os.environ[conf.param_to_env_name("intparam")] = "10"
        self.assertEqual(conf["intparam"], 10)


    def test_load_yml(self):
        from tests._configExample import MyConfig2
        class _MyConfig2(MyConfig2): pass
        conf = _MyConfig2(config_file=os.path.join(os.path.dirname(__file__),"data/myconfig2.yaml"))
        # print(conf.all_parameters_dict)
        self.assertEqual(conf["intparam"], -1)
        self.assertEqual(conf["plist"], [-1, "tryStr"])

    def test_update(self):
        from tests._configExample import MyConfig2
        conf = MyConfig2()
        conf.update(dict(intparam=-1, plist=[-1, "tryStr"]))
        self.assertEqual(conf["intparam"], -1)
        self.assertEqual(conf["plist"], [-1, "tryStr"])

    def test_argparse(self):

        from tests._configExample import MyConfig1
        from typing import Optional
        from argparse import ArgumentParser

        class _MyConfig1(MyConfig1):
            def set_parameters(self):
                super().set_parameters()
                self.null_param:Optional[int] = None
        conf = _MyConfig1()
        self.assertEqual(conf.caca, "tua")
        parser = ArgumentParser()
        conf.add_args_to_argparse(parser)
        # parser.print_help()
        pars = parser.parse_args(["--null_param", "3"])
        self.assertEqual(pars.null_param, 3)

        pars = parser.parse_args(["--param1", "32"])
        self.assertEqual(pars.param1, "32")

        class _MyConfig3(MyConfig1):
            def set_parameters(self):
                self.one_list:List[float]=[1.,12.]
                self.null_list:Optional[List[float]]=None

        conf = _MyConfig3()
        parser = ArgumentParser()
        conf.add_args_to_argparse(parser)
        parser.print_help()
        pars = parser.parse_args(["--one_list", "3", "82"])
        self.assertAlmostEqual(sum(pars.one_list), sum([3, 82]))

        pars = parser.parse_args(["--null_list", "3", "82"])
        self.assertAlmostEqual(sum(pars.null_list), sum([3, 82]))
