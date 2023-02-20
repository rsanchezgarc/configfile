from configfile.configbase import ConfigBase


class MyConfig1(ConfigBase):

    def set_parameters(self):
        self.conf1Int = 1
        self.conf1Str = "caca"
        self.conf1List = [1,2,3]


conf = MyConfig1()
