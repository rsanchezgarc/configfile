import json


def param_to_env_name(prefix, prefix_sep, paramname):
    return prefix + prefix_sep + paramname

def env_to_param_name(envname, prefix_sep):
    prefix, varname = envname.split(prefix_sep)
    return varname

def serialize_param_to_envvar(v):
    return json.dumps(v)

def parse_envvar_to_param(v):
    return json.loads(v)