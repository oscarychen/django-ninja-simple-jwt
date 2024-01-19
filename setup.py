from setuptools import find_packages, setup

setup(
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "docs")),
)
