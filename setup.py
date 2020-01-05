from setuptools import setup, find_packages

setup(
    name='circum',
    version='{tag}',
    author="Lane Haury",
    author_email="lane@lumineerlabs.com",
    description= "Circum is a set of tools for detecting and tracking moving objects" +
                 "via a variety of distributed sensors.",
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
        'setuptools-git-version'
    ],
    entry_points='''
        [console_scripts]
        circum-endpoint=circum.endpoint:cli
        circum-service=circum.service:cli
    ''',
)
