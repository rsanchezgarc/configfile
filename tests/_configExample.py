from typing import Optional, List

from configfile.configbase import ConfigBase


class MyConfig1(ConfigBase):

    def set_parameters(self):
        self.conf1Int = 1
        self.conf1Str = "caca"
        self.conf1List = [1,2,3]


class MyConfig2(ConfigBase):

    def set_parameters(self):
        self.conf2Int:int = 2
        self.conf2Str = "tua"
        self.conf2List:Optional[List[int]] = None


if __name__ == "__main__":
    conf2 = MyConfig2("MyConfig2")
    print(conf2.conf2Int)
    print(conf2.conf2Str)


    class MyConf3(ConfigBase):
        def set_parameters(self):
            self.myParam:str = "3"
            self.myParamNot:Optional[str] = None
            self._add_params_from_other_config(conf2)

    conf3 = MyConf3()
    print(conf3.myParam)
    print(conf3.MyConfig2__conf2List)
    print(conf3.MyConfig2__conf2Str)
    print(conf3.all_parameters_dict)
