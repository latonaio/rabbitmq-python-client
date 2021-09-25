# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Iterable, Set

import aio_pika
from aiostream import stream

from .exceptions import RabbitmqConnectionError, QueueNotFoundError


# dict を Message に変換する
# RabbitMQ が再起動してもメッセージが消えてしまわないよう、
# 永続的 (PERSISTENT) を指定する
def _serialize(data: Any) -> aio_pika.Message:
	binary = json.dumps(data, ensure_ascii=False).encode('utf-8')
	message = aio_pika.Message(
		binary,
		delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
		content_type='application/json'
	)
	return message


def _deserialize(data: aio_pika.IncomingMessage) -> Any:
	return json.loads(data.body.decode('utf-8'))


class RabbitmqMessage:
	def __init__(self, message: aio_pika.IncomingMessage, data: Any):
		self.message = message
		self.data = data

	@property
	def queue_name(self) -> str:
		return self.message.routing_key

	@property
	def is_responded(self) -> bool:
		return self.message.processed

	def process(self, *args, **kwargs):
		return self.message.process(*args, **kwargs)

	async def success(self):
		await self.message.ack()

	async def fail(self):
		await self.message.reject()

	async def requeue(self):
		await self.message.reject(requeue=True)


class RabbitmqClient:
	def __init__(self, connection: aio_pika.RobustConnection, channel: aio_pika.Channel, receive_queues: Set[str], send_queues: Set[str]):
		self.connection = connection
		self.channel = channel
		self.receive_queues = receive_queues
		self.send_queues = send_queues

	@classmethod
	async def create(cls, url: str, receive_queues: Iterable[str] = None, send_queues: Iterable[str] = None, prefetch_count: int = 1) -> RabbitmqClient:
		receive_queues = set(receive_queues or [])
		send_queues = set(send_queues or [])
		queues = set([*receive_queues, *send_queues])

		# 接続
		try:
			connection = await aio_pika.connect_robust(url, loop=asyncio.get_event_loop())
			channel = await connection.channel()

			# メッセージを同時に受け取る個数を指定
			await channel.set_qos(prefetch_count=prefetch_count)
		except Exception as e:
			raise RabbitmqConnectionError(e) from e

		# キューの存在確認
		try:
			for queue_name in queues:
				await channel.get_queue(queue_name, ensure=True)
		except Exception as e:
			raise QueueNotFoundError(e) from e

		return cls(connection, channel, receive_queues, send_queues)

	async def iterator(self):
		async def receive(queue_name: str):
			queue: aio_pika.Queue = await self.channel.get_queue(queue_name, ensure=True)
			async with queue.iterator() as queue_iter:
				async for message in queue_iter:
					yield message

		# 呼び出し元にメッセージを順に渡す
		async with stream.merge(
			*(receive(queue_name) for queue_name in self.receive_queues)
		).stream() as streamer:
			streamer: AsyncIterator[aio_pika.IncomingMessage]
			async for message in streamer:
				try:
					data = _deserialize(message)
				except Exception:
					print('[RabbitmqClient] message deserialization failed, ignoring!')
					continue

				# エラー時の ack, reject は message.process() 等で利用側で行う想定
				yield RabbitmqMessage(message, data)

	async def send(self, queue_name: str, data: Any):
		if queue_name not in self.send_queues:
			raise QueueNotFoundError(f'queue_name not passed to create(): {queue_name}')

		await self.channel.default_exchange.publish(
			_serialize(data),
			routing_key=queue_name
		)

	async def close(self):
		await self.channel.close()
		await self.connection.close()
