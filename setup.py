"""A setuptools based setup module.
"""

from pathlib import Path
from setuptools import setup, find_namespace_packages

here = Path(__file__).parent.absolute()

# Get the long description from the README file
with open(here.joinpath('README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='w4un_hydromet_impact',

    version='0.1.0',

    description='Weather4UN global impact estimates',

    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/ThomasRoosli/Weather4UN_global_impact_estimates',

    author='MeteoSwiss',
    author_email='https://github.com/ThomasRoosli/Weather4UN_global_impact_estimates',

    license='OSI Approved :: GNU Lesser General Public License v3 (GPLv3)',

    classifiers=[
        'Programming Language :: Python :: 3.9',
    ],

    keywords='severe weather impact',

    python_requires=">=3.9,<3.12",

    install_requires=[
        'climada==4.1.1',
        'pydantic',
    ],

    extras_require={
    },

    packages=find_namespace_packages(include=['w4un_hydromet_impact*']),

    setup_requires=['setuptools_scm'],
    include_package_data=True,
)
