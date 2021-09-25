# -*- coding: utf-8 -*-

class RabbitmqClientError(Exception):
	pass


class RabbitmqConnectionError(RabbitmqClientError):
	pass


class QueueNotFoundError(RabbitmqClientError):
	pass
