from os.path import dirname, abspath, join
from setuptools import setup

with open(abspath(join(dirname(__file__), 'README.md'))) as fileobj:
    README = fileobj.read().strip()

setup(
    name='hlsclient',
    description='Client to download all files from HLS streams',
    long_description=README,
    author='Globo.com',
    url='https://github.com/globocom/hlsclient',
    version='0.1.1',
    zip_safe=False,
    include_package_data=True,
    packages=[
        'hlsclient',
        ],
    install_requires=[
        'requests==0.11.2',
        'm3u8==0.1.0',
        ],
)
