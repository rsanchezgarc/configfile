ALLOWED_TYPES = (int, str, bool, float) #, type(None))
ALLOWED_TYPE_NAMES = [x.__name__ for x in ALLOWED_TYPES]
VALID_ANNOTATION_LIST_REGEX_PATT = r"(List|Tuple)\[(\w+)\]"
PREFIX_ENV_SEP = "___"  # Access it only with ConfigBase.PREFIX_ENV_SEP
NESTED_SEPARATOR = "__"  # Access it only with ConfigBase.NESTED_SEPARATOR