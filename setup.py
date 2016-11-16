#!/usr/bin/env python
# coding: utf-8

import os

from io import open
from setuptools import setup, find_packages


here = os.path.dirname(__file__)

with open(os.path.join(here, 'README.rst'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='kostyor-openstack-ansible',
    version='0.1.0',
    description='OpenStack Ansible driver for Kostyor',
    long_description=long_description,
    license='GPLv3',
    url='http://github.com/ikalnytskyi/kostyor-openstack-ansible/',
    keywords='openstack kostyor driver ansible upgrade day2 ops',
    author='Ihor Kalnytskyi',
    author_email='igor@kalnitsky.org',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    zip_safe=False,
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'ansible >= 2.1',
        'kostyor == dev',
    ],
    tests_require=[
        'mock >= 2.0',
        'pytest >= 3.0',
    ],
    dependency_links=[
        # Kostyor is not released yet, so in order to perform tests we
        # need to install it at least from master branch.
        'git+https://github.com/sc68cal/Kostyor.git#egg=kostyor-dev',
    ],
    entry_points={
        'kostyor.upgrades.drivers': [
            'openstack-ansible = kostyor_openstack_ansible.upgrade:Driver',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
    ],
)
