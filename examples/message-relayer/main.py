#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os

# ## 概要
# queue_from から読み取ったメッセージをそのまま
# queue_to に書き込むサンプルプログラム
#
# ## ローカルでの実行方法
# bash launch.sh
#
# ## 環境変数
# 環境変数に次の値をセットして実行
# (launch.sh 内では自動でセットされます)
#
# ### このプログラム固有の環境変数
# * RABBITMQ_URL: amqp://[ユーザ名]:[パスワード]@[端末の IP アドレス or RabbitMQのpod名]:[ポート番号]/[バーチャルホスト名]
# * QUEUE_FROM: キューの読み込み元
# * QUEUE_TO: キューの書き込み先


from rabbitmq_client import RabbitmqClient


async def main():
	# amqp://[ユーザ名]:[パスワード]@[端末の IP アドレス or RabbitMQのpod名]:[ポート番号]/[バーチャルホスト名]
	url = os.environ['RABBITMQ_URL']
	# キューの読み込み元
	queue_from = os.environ['QUEUE_FROM']
	# キューの書き込み先
	queue_to = os.environ['QUEUE_TO']

	# クライアントの作成: 読み込み元、読み出し先を指定する
	# (指定しなくていい場合は None を指定)
	client = await RabbitmqClient.create(url, {queue_from}, {queue_to})

	# queue_from からメッセージが到着するたびにこの for 文が動く
	# メッセージは不可視状態になるが、キューに残っている
	async for message in client.iterator():
		try:
			# この with ブロックから抜けたとき、キューからメッセージが消去される
			# 例外が原因で with ブロックを抜けた際は、
			# メッセージがデッドレターという別のキューに入る（設定されている場合）
			#
			# 何らかの理由でメッセージを後から再処理したいとき等、
			# 再度キューに戻すときは、message.requeue() をこの with ブロック内で実行する
			async with message.process():
				print('received from:', message.queue_name)
				print('data:', message.data)

				# 受け取ったメッセージをそのまま queue_to にコピー
				# data には JSON に変換できる値を渡してください
				await client.send(queue_to, message.data)
				print('sent:')

			print('removed:')

		except Exception as e:
			print('errored:', e)


# aion 経由で実行されるときは以下を追加
# @main_decorator(SERVICE_NAME, WITHOUT_KANBAN)
def main_wrapper():
	# 非同期関数を呼び出し、終わるまで待つ
	# ※ main の開始時のみの利用にとどめ、他では await を使ってください
	#
	# 参考
	# https://docs.python.org/ja/3/library/asyncio-task.html#asyncio.run
	asyncio.run(main())


if __name__ == '__main__':
	main_wrapper()
