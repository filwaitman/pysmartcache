from setuptools import setup

VERSION = '0.4'


setup(
    name='pysmartcache',
    packages=['pysmartcache', ],
    version=VERSION,
    author='Filipe Waitman',
    author_email='filwaitman@gmail.com',
    install_requires=[x.strip() for x in open('requirements.txt').readlines()],
    tests_require=[x.strip() for x in open('requirements_test.txt').readlines()],
    url='https://github.com/filwaitman/pysmartcache',
    download_url='https://github.com/filwaitman/pysmartcache/tarball/{}'.format(VERSION),
    keywords=['cache', 'caching', 'memcached'],
    test_suite='tests',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ]
)
