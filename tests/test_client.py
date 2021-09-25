#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import AsyncMock, Mock, NonCallableMock, patch

import aio_pika

from rabbitmq_client import RabbitmqClient


URL = 'amqp://username:password@hostname:5672/virtualhost'
QUEUE_FROM = 'receive_queue'
QUEUE_TO = 'send_queue'

DATA_BYTES = b'{"test": "hello world"}'
DATA_DICT = {'test': 'hello world'}


async def async_repeat(data):
	while True:
		yield data


class MockMessage:
	def __init__(self, routing_key, body):
		self.routing_key = routing_key
		self.body = body

	def process(self, *args, **kwargs):
		return self

	async def __aenter__(self):
		return self

	async def __aexit__(self, *exc_info):
		pass


class MockManager:
	def __init__(self):
		self.iterator = AsyncMock()
		self.iterator.__aenter__.return_value = async_repeat(
			MockMessage(QUEUE_FROM, DATA_BYTES)
		)

		self.queue = NonCallableMock(spec=aio_pika.RobustQueue)
		self.queue.iterator = Mock(return_value=self.iterator)

		self.channel = NonCallableMock(spec=aio_pika.RobustChannel)
		self.channel.get_queue = AsyncMock(return_value=self.queue)
		self.exchange = self.channel.default_exchange = Mock(
			spec=aio_pika.RobustExchange
		)

		self.connection = NonCallableMock(spec=aio_pika.RobustConnection)
		self.connection.channel = AsyncMock(return_value=self.channel)

		self.connect_robust = AsyncMock(return_value=self.connection)

	def patch(self):
		return patch('aio_pika.connect_robust', self.connect_robust)


class TestRabbitmqClient(unittest.IsolatedAsyncioTestCase):
	async def test_receive(self):
		mocks = MockManager()
		with mocks.patch():
			### テスト対象コード
			client = await RabbitmqClient.create(URL, {QUEUE_FROM}, {})
			async for message in client.iterator():
				async with message.process():
					break
			await client.close()

		### 検証
		# 受信元キュー名の検証
		self.assertEqual(message.queue_name, QUEUE_FROM)
		# デコード済みデータの検証
		self.assertEqual(message.data, DATA_DICT)

	async def test_send(self):
		mocks = MockManager()
		with mocks.patch():
			### テスト対象コード
			client = await RabbitmqClient.create(URL, {}, {QUEUE_TO})
			await client.send(QUEUE_TO, DATA_DICT)
			await client.close()

		### 検証
		message = mocks.exchange.publish.call_args.args[0]
		routing_key = mocks.exchange.publish.call_args.kwargs['routing_key']

		# 送信先を検証
		self.assertEqual(routing_key, QUEUE_TO)
		# データタイプに JSON が指定されているか検証
		self.assertEqual(message.content_type, 'application/json')
		# 永続化の指定を検証
		self.assertEqual(message.delivery_mode, aio_pika.DeliveryMode.PERSISTENT)
		# エンコード済みデータの検証
		self.assertEqual(message.body, DATA_BYTES)


if __name__ == '__main__':
	unittest.main()
