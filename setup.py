from setuptools import find_packages, setup
from _version import __version__, __description__, __tool_name__

ws_name = "wi_sync"
with open("requirements.txt",'r', encoding='UTF-8', errors='ignore') as file:
  lines = file.readlines()
  lines = [line.rstrip() for line in lines]

setup(
  name=f'ws_{__tool_name__}',
  entry_points={
    'console_scripts': [
      f'{__tool_name__}=ws_{ws_name}.ws_{__tool_name__}:main'
    ]},
  packages=find_packages(),
  version= __version__,
  author="WhiteSource Professional Services",
  author_email="ps@whitesourcesoftware.com",
  description=__description__,
  license='LICENSE.txt',
  python_requires='>=3.7',
  long_description=open("README.md").read(),
  long_description_content_type="text/markdown",
  install_requires=lines,
  classifiers=[
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
  ],
)