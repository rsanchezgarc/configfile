# configfile

This is a simple package to manage configurations.


### Usage
First, define a child class of `ConfigBase` than implements `set_parameters(self)`.
This methods sets all parameters to be handled in the configuration just with the typical 
`self.param_name=value`

Then the configuration parameters can be accessed using the dot or bracket access

It can also allow for dynamic change of the parameters as it were a dictionary
and from environmental variables named NAME___PARAMENTERNAME, where NAME is provided
by the user