from setuptools import find_packages, setup  # pylint: disable=import-error,E0401

setup(
    name="django-ninja-simple-jwt",
    version="0.7.1",
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "docs")),
)
