import os.path

with open(os.path.abspath(os.path.join(__file__, os.path.pardir, "version.txt"))) as f:
    __version__ = f.read().strip()

from configfile.configbase import ConfigBase
