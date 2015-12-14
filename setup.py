from setuptools import setup


setup(
    name='pysmartcache',
    packages=['pysmartcache', ],
    version='0.1',
    description='PySmartCache is a way to get automatic caching and caching invalidation for functions/methods.',
    author='Filipe Waitman',
    author_email='filwaitman@gmail.com',
    install_requires=open('requirements.txt').readlines(),
    tests_require=open('requirements_test.txt').readlines(),
    url='https://github.com/filwaitman/pysmartcache',
    download_url='https://github.com/filwaitman/pysmartcache/tarball/0.1',
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
