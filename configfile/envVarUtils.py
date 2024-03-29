import json
import ast

def param_to_env_name(prefix, prefix_sep, paramname):
    return prefix + prefix_sep + paramname

def env_to_param_name(envname, prefix_sep):
    try:
        prefix, varname = envname.split(prefix_sep)
    except ValueError:
        raise ValueError(f"Error, env_to_param_name failed for {envname} using prefix_sep {prefix_sep}")
    return varname

def serialize_param_to_envvar(v):
    return json.dumps(v)

def load_envvar_to_param(v):
    return json.loads(v)

def load_envvar(envVal):
    return ast.literal_eval(envVal)