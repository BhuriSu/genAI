from src.constants import (
    URL_API,
    PATH_LAST_PROCESSED,
    MAX_LIMIT,
)

import kafka.errors
import json
import datetime
import requests
from kafka import KafkaProducer
from typing import List
import logging

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO, force=True)


def get_latest_timestamp():
    """
    Gets the latest timestamp from the last_processed.json file
    """
    with open(PATH_LAST_PROCESSED, "r") as file:
        data = json.load(file)
        if "last_processed" in data:
            return data["last_processed"]
        else:
            return datetime.datetime.min


def get_all_data(last_processed_timestamp: datetime.datetime) -> List[dict]:
    n_results = 0
    full_data = []
    while True:
        # The publication date must be greater than the last processed timestamp and the offset (n_results)
        # corresponds to the number of results already processed.
        url = URL_API.format(last_processed_timestamp, n_results)
        response = requests.get(url)
        data = response.json()
        current_results = data["results"]
        full_data.extend(current_results)
        n_results += len(current_results)
        if len(current_results) < MAX_LIMIT:
            break

    logging.info(f"Got {len(full_data)} results from the API")

    return full_data


def deduplicate_data(data: List[dict]) -> List[dict]:
    return list({v["id"]: v for v in data}.values())


def query_data() -> List[dict]:
    """
    Queries the data from the API
    """
    last_processed = get_latest_timestamp()
    full_data = get_all_data(last_processed)
    full_data = deduplicate_data(full_data)
    if full_data:
        return full_data
        
def create_kafka_producer():
    """
    Creates the Kafka producer object
    """
    try:
        producer = KafkaProducer(bootstrap_servers=["kafka:9092"])
    except kafka.errors.NoBrokersAvailable:
        logging.info(
            "We assume that we are running locally, so we use localhost instead of kafka and the external "
            "port 9094"
        )
        producer = KafkaProducer(bootstrap_servers=["localhost:9094"])

    return producer


def stream():
    """
    Writes the API data to Kafka topic list_breweries
    """
    producer = create_kafka_producer()
    results = query_data()
    kafka_data_full = map(results)
    for kafka_data in kafka_data_full:
        producer.send("list_breweries", json.dumps(kafka_data).encode("utf-8"))


if __name__ == "__main__":
    stream()
