#!/bin/bash

cd "$(dirname "$0")"

if [ ! -f venv/bin/activate ]; then
	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.txt
else
	source venv/bin/activate
fi


echo "Launching main.py..."

RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/%2F \
QUEUE_TO=test_a \
TICK_INTERVAL=5 \
	python main.py
