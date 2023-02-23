from configfile.configbase import ConfigBase


class MyConfig1(ConfigBase):

    def set_parameters(self):
        self.conf1Int = 1
        self.conf1Str = "caca"
        self.conf1List = [1,2,3]


conf = MyConfig1()

if __name__ == "__main__":
    print(conf.conf1List)
    print(conf.name)
    conf.conf1Int = 10
    assert "conf1Int" not in conf.__dict__
    print(conf.conf1Int)
    print("Done")

