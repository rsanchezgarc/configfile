from configfile.configbase import ConfigBase


class MyConfig1(ConfigBase):

    def set_parameters(self):
        self.param1 = "Hola"
        self.caca = "tua"

class MyConfig2(ConfigBase):

    def set_parameters(self):
        self.intparam = 1
        self.strparam = "tua"
        self.plist = [1,2,3]
