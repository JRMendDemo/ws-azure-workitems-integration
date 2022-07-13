from setuptools import find_packages, setup
from ws_azure_workitems_integration._version import __version__, __description__, __tool_name__

ws_name = f"ws_{__tool_name__}"
with open("requirements.txt",'r', encoding='UTF-8', errors='ignore') as file:
  lines = file.readlines()
  lines = [line.rstrip() for line in lines]

setup(
  name=ws_name,
  entry_points={
    'console_scripts': [
      f'{__tool_name__}={ws_name}.ws_{__tool_name__}:main'
    ]},
  packages=find_packages(),
  version= __version__,
  author="WhiteSource Professional Services",
  author_email="ps@whitesourcesoftware.com",
  description=__description__,
  license='LICENSE.txt',
  python_requires='>=3.9',
  long_description=open("README.md").read(),
  long_description_content_type="text/markdown",
  install_requires=lines,
  classifiers=[
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
  ],
)