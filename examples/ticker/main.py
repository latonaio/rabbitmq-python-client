#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import datetime
import os

from rabbitmq_client import RabbitmqClient

# ## 概要
# queue_to に
# tickInterval の間隔で時刻を書き込むサンプルプログラム
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
# * QUEUE_TO: キューの書き込み先
# * TICK_INTERVAL: 書き込み間隔


def getTickInterval():
	try:
		interval = float(os.environ['TICK_INTERVAL'])
		return interval
	except Exception:
		interval = 5
		return interval


async def main():
	# amqp://[ユーザ名]:[パスワード]@[端末の IP アドレス or RabbitMQのpod名]:[ポート番号]/[バーチャルホスト名]
	url = os.environ['RABBITMQ_URL']
	# キューの書き込み先
	queue_to = os.environ['QUEUE_TO']
	# 書き込み間隔
	tickInterval = getTickInterval()

	# クライアントの作成: 読み込み元、読み出し先を指定する
	# (指定しなくていい場合は None を指定)
	client = await RabbitmqClient.create(url, {}, {queue_to})

	while True:
		await asyncio.sleep(tickInterval)
		now = datetime.datetime.now().isoformat()
		# data には JSON に変換できる値を渡してください
		data = dict(time=now)
		await client.send(queue_to, data)
		print('sent:' + data['time'])
    

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
