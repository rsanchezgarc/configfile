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




if __name__ == "__main__":
    conf = MyConfig2("MyConfig2")
    print(conf.intparam)
    print(conf.strparam)


    class MyConf3(ConfigBase):
        def set_parameters(self):
            self.myParam = "3"
            self.add_params_from_other_config(conf)

    conf3 = MyConf3()
    print(conf3.myParam)
    print(conf3.MyConfig2_plist)
    print(conf3.MyConfig2_strparam)
