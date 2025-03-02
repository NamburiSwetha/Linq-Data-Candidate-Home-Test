# -*- coding: utf-8 -*-
"""Kafka.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1PSZ8TEIru7BsrnikGIiDoQs4O8Ix_bba
"""

pip install kafka-python

from kafka import KafkaConsumer, KafkaProducer
import json
from collections import deque

# Initialize Kafka consumer to read old events
consumer = KafkaConsumer(
    "stock_price_topic",
    bootstrap_servers="localhost:9092",
    group_id="recovery-group",
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

# Initialize Kafka producer to send corrected data
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    enable_idempotence=True
)

# Define moving average parameters
WINDOW_SIZE = 5
stock_history = {}

# Function to calculate moving average over the last N records
def calculate_moving_average(stock, price):
    if stock not in stock_history:
        stock_history[stock] = deque(maxlen=WINDOW_SIZE)
    stock_history[stock].append(price)
    return sum(stock_history[stock]) / len(stock_history[stock])

# Read and process past events
for message in consumer:
    event = message.value
    stock = event["stock"]
    price = event["price"]

    # Compute corrected moving average
    corrected_avg = calculate_moving_average(stock, price)

    # Prepare corrected event
    corrected_data = {
        "stock": stock,
        "corrected_moving_avg": corrected_avg,
        "timestamp": event["timestamp"]
    }

    # Send corrected data to Kafka
    producer.send("corrected_stock_price_topic", value=corrected_data, key=stock.encode())

    print(f"Reprocessed {stock}: New Moving Avg = {corrected_avg}")

consumer = KafkaConsumer(
    "corrected_stock_price_topic",
    bootstrap_servers="localhost:9092",
    group_id="processing-group",
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

# Continuously process corrected stock data
for message in consumer:
    corrected_event = message.value
    print(f"Processing Corrected Event: {corrected_event}")