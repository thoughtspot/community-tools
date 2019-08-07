from setuptools import setup, find_packages

setup(
    name='tql',
    version='1.0',
    description='This package contains tools for using ThoughtSpot query langauge (TQL) and loading tools.',
    long_description_content_type="text/markdown",
    url='https://thoughtspot.com',
    author='Bill Back',
    author_email='bill.back@thoughtspot.com',
    license='MIT',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        "paramiko"
    ]
)
