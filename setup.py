#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
	name='rabbitmq_client',
	version='0.1.0',
	description='RabbitMQ client',
	long_description='RabbitMQ client',
	packages=['rabbitmq_client'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'aio-pika==6.*',
		'aiostream==0.4.3',
	],
	entry_points='''
''')
