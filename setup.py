from setuptools import setup, find_packages

setup(
    name='circum',
    version='0.1',
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'zeroconf',
        'click'
        ],
    author="Lane Haury",
    author_email="lane@lumineerlabs.com",
    description="",
    url="https://github.com/LumineerLabs/circum",
)