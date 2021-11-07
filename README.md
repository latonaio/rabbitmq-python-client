# rabbitmq-python-client  

rabbitmq-python-client は、RabbitMQ に接続し、メッセージを送受信するためのシンプルな、Python 3 ランタイム のための ライブラリです。  


## 動作環境
* OS: Linux
* CPU: ARM/AMD/Intel
* Python Runtime 3.7 以降  


## 導入方法  

pip でインストールしてください。  

```sh
pip install "git+https://github.com/latonaio/rabbitmq-python-client.git@main#egg=rabbitmq_client"
```

`requirements.txt` を利用する場合、上の git から始まる URL をそのまま記載してください。  


## 使用方法

### ライブラリの初期化

`RabbitmqClient` を import します。

```py
from rabbitmq_client import RabbitmqClient
```

`await RabbitmqClient.create('<URL>', ['<受信するキュー名>'...], ['<送信するキュー名>'...])` でクライアントを作成します。

指定するキューは事前に存在している必要があります。存在しない場合は例外が発生します。

例:

```py
client = await RabbitmqClient.create(
	'amqp://username:password@hostname:5672/virtualhost',
	['queue_from'],
	['queue_to']
)
```


### キューからメッセージを受信

メッセージは次の 2 通りの方法で受け取ることができます。

`message.queue_name` に受け取り元キューの名前が、`message.data` に受信したデータが格納されています。


#### 方法 1: 結果通知を自動で行う (推奨)

次のようなループでメッセージを処理します。ループと `async with` 文を組み合わせることで、メッセージ処理後に本来行うべき RabbitMQ への処理結果の通知をライブラリ側に任せることができます。

例:

```py
async for message in client.iterator():
	try:
		# この with ブロックから抜けたとき、キューからメッセージが消去される
		# 例外が原因で with ブロックを抜けた際は、
		# メッセージがデッドレターという別のキューに入る (定義されている場合)
		#
		# 何らかの理由でメッセージを後から再処理したいとき等、
		# 再度キューに戻すときは、await message.requeue() をこの with ブロック内で実行する
		async with message.process():
			# 何らかの処理
			print(f'received from {message.queue_name}')
			print('data:', message.data)

	except Exception:
		print('failed!')
```


#### 方法 2: 結果通知を手動で行う

方法 1 と同じように、次のようなループでメッセージを処理します。

メッセージの処理が終わったあと、必ず結果を通知するメソッド (`await message.success()`, `await message.fail()` または `await message.requeue()`) をコールしてください。`success()` の場合はキューからそのメッセージが正常に削除され、`fail()` の場合はそのメッセージがデッドレターに送られます (設定されている場合) 。

(何らかの理由で再度メッセージをキューに戻したいときは、`await message.requeue()` をコールしてください。)

例:

```py
async for message in client.iterator():
	# 何らかの理由でメッセージを後から再処理したいとき等、
	# 再度キューに戻すときは、await message.requeue() を実行する
	try:
		# 何らかの処理
		print(f'received from {message.queue_name}')
		print('data:', message.data)

		# 処理成功
		await message.success()

	except Exception:
		# 処理失敗
		# メッセージがデッドレターという別のキューに入る (定義されている場合)
		await message.fail()

		print('failed!')
```


### メッセージを送信する

`await client.send('<送信先キュー名>', <データ>)` のように呼び出してください。`<データ>` には JSON 化できるオブジェクト (dict, list 等) を渡します。

例:

```py
payload = {
	'hello': 'world'
}
await client.send('queue_to', payload)
```


### 接続を終了する

`close()` メソッドを呼び出してください。

```py
await client.close()
```
