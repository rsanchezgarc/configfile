# configfile

This is a simple package to manage configurations.


### Usage
First, define a child class of `ConfigBase` than implements `set_parameters(self)`.
This methods sets all parameters to be handled in the configuration just with the typical 
`self.param_name=value`

```
from configfile.configbase import ConfigBase

class MyConfig(ConfigBase):
    def set_parameters(self):
        self.floatParam=1. #The type will be automatically inferred if no type hint provided
        self.intParam=1
        self.intParamNoneDefault:Optional[int]=None #Type hints required if the argument is set to None
        self.listParam:List[float]=[1.,12.] #Type hint is not required here, but still useful
        
```
Then the configuration parameters can be accessed using the dot or bracket access

It can also allow for dynamic change of the parameters as it were a dictionary
and from environmental variables named NAME___PARAMETERNAME, where NAME is provided
by the user at building time. Dicts are flattened by adding "__" between different levels


It also allow to generate an automatic argument parser:
```
from configfile.configbase import ConfigBase
from argparse import ArgumentParser

class MyConfig(ConfigBase):
    def set_parameters(self):
        self.floatParam=1. #The type will be automatically inferred if no type hint provided
        self.one_list:List[float]=[1.,12.]
        self.null_list:Optional[List[float]]=None
        
conf = MyConfig(name="NAME_TO_BE_USED_IN_ENV_VARS")
parser = ArgumentParser()
conf.add_args_to_argparse(parser)
parser.print_help()
pars = parser.parse_args(["--one_list", "3", "82"])
assert abs(sum(pars.one_list) - sum([3, 82])) < 0.001
```