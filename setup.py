from setuptools import setup, find_packages

setup(
    name = 'mp3rescene',

    version = '0.0.1',
    description = 'turn broken or renamed scene releases back into their original glory with the aid of pyRescene and srrdb.com',
    author = 'gunnar',
    license = 'NONE',
    #url = 'https://github.com/stickin/pyautorescene',
    packages = find_packages(),
    scripts = ['bin/mp3rescene.py'],

    keywords = ['rescene', 'srr', 'srs', 'scene', 'mp3', 'music', 'auto'],
    install_requires = ['requests', 'colorama'],
    # requests is used for HTTP requests to srrdb.com
    # colorama is used for pretty printing in verbose mode
)
