from os.path import dirname, abspath, join
from setuptools import setup

with open(abspath(join(dirname(__file__), 'README.md'))) as fileobj:
    README = fileobj.read().strip()

setup(
    name='hlsclient',
    description='Client to download all files from HLS streams',
    long_description=README,
    url='https://github.com/globocom/hlsclient',
    version='0.0',
    zip_safe=False,
    packages=[
        'hlsclient',
        'hlsclient.discover'
        ],
    install_requires=[
        'requests==0.11.2',
        'm3u8==0.0',
        'fms==0.0.1',
        ],
    dependency_links=[
        'http://github.com/globocom/m3u8/tarball/master#egg=m3u8-0.0',
        'http://github.com/jbochi/fms/tarball/master#egg=fms-0.0.1',
        ],
)
