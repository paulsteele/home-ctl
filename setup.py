from setuptools import setup, find_packages # type:ignore

setup(
  name="Home Controller",
  version="1.0.0",
  packages=find_packages(),
  entry_points='''
    [console_scripts]
    homectl=home.control:cli
  ''',
  package_data={
    '': ['resource_creation.jinja']
  }
)
