# Streaming Tourist Area Processing 
## Used Technologies and Services

- Apache Airflow
- Apache Zookeeper
- Apache Kafka
- Apache Spark 
- Elasticsearch
- Kibana
- MinIO
- Docker

## Overview

- Take a compressed data source from a URL
- Process the raw data with **PySpark**
- Use **data-generator** to simulate streaming data, and send the data to **Apache Kafka**.
- Read the streaming data from Kafka topic using **PySpark (Spark Streaming)**.
- Write the streaming data to **Elasticsearch**, and visualize it using **Kibana**.
- Write the streaming data to **MinIO (AWS Object Storage)**.
- Use **Apache Airflow** to orchestrate the whole data pipeline.



