from setuptools import setup, find_packages
from os import path


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='circum',
    version_format='{tag}',
    author="Lane Haury",
    author_email="lane@lumineerlabs.com",
    description="Circum is a set of tools for detecting and tracking moving objects" +
                "via a variety of distributed sensors.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/LumineerLabs/circum",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'zeroconf',
        'click',
        'numpy',
        'scipy',
        'pykalman',
        'munkres',
        'bson',
        'mock',
        'matplotlib',
        'setuptools-git-version',
    ],
    entry_points={
        'console_scripts': [
            'circum-endpoint=circum.endpoint:cli',
            'circum=circum.service:cli'
        ],
        'circum.sensors': [
            'simulator=circum.sensors.simulator:simulator',
        ],
    },
)
