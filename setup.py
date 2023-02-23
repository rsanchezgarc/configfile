import importlib
import os

import setuptools
from setuptools import setup

def version():
    with open(os.path.abspath(os.path.join(__file__, os.path.pardir, "configfile", "version.txt"))) as f:
        version = f.read().strip()
    return version

def readme():
  readmePath = os.path.abspath(os.path.join(__file__, "..", "README.md"))
  try:
    with open(readmePath) as f:
      return f.read()
  except UnicodeDecodeError:
    try:
      with open(readmePath, 'r', encoding='utf-8') as f:
        return f.read()
    except Exception as e:
      return "Description not available due to unexpected error: "+str(e)

install_requires = ["pyyaml==6.0", "argparse"]

setup(name='configfile',
      version=version(),
      description='Flexible configuration file managment',
      long_description=readme(),
      long_description_content_type="text/markdown",
      keywords='config file',
      url='https://github.com/rsanchezgarc/configfile',
      author='Ruben Sanchez-Garcia',
      author_email='ruben.sanchez-garcia@stats.ox.ac.uk',
      license='MIT',
      packages=setuptools.find_packages(),
      install_requires=install_requires,
      dependency_links=[],
      include_package_data=True,
      zip_safe=False)

