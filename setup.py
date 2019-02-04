from setuptools import find_packages, setup

version = {}
with open("cors/version.py") as fp:
    exec(fp.read(), version)

description = "Utilities for creating CORS-enabled HTTP interfaces"
long_description = """{}

This package aims to help developers improve automated HTTP API tests by being
able to automatically test that any request can also be made from browsers
with scripts on other origins.

This package is based on code from https://github.com/synacor/python-cors
""".format(description)

setup(
    name="cors.testing",
    version=version['__version__'],
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Nick Coutsos",
    author_email="ncoutsos@synacor.com",
    url='https://github.com/bendikro/python-cors',
    packages=find_packages(exclude=["*tests*"]),
    install_requires=['future', 'requests', 'tornado'],
    tests_require=['mock'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing :: Unit"
    ],
)
