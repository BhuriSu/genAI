# Building a simple End-to-End Data Engineering System 
This project uses different tools such as kafka, airflow, spark, postgres and docker. 

## Overview

1. Data Streaming: Initially, data is streamed from the API into a Kafka topic.
  
2. Data Processing: A Spark job then takes over, consuming the data from the Kafka topic and transferring it to a PostgreSQL database.
   
3. Scheduling with Airflow: Both the streaming task and the Spark job are orchestrated using Airflow. While in a real-world scenario, the Kafka producer would constantly listen to the API, for demonstration purposes, we'll schedule the Kafka streaming task to run daily. Once the streaming is complete, the Spark job processes the data, making it ready for use by the LLM application.

All of these tools will be built and run using docker, and more specifically docker-compose.

## How to run this etl process

1. run in terminal >> docker network create airflow-kafka
2. run in terminal >> docker-compose up (you can see kafka ui and config in http://localhost:8800/ )
3. python scripts/create_table.py for creating table in pgAdmin4 
4. run in terminal >> docker build -f spark/Dockerfile -t list_breweries/spark:latest --build-arg POSTGRES_PASSWORD={your_password} . 
5. rin in bash >> echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_PROJ_DIR=\"./airflow_resources\"" > .env
6. run in terminal >>  docker compose -f docker-compose-airflow.yaml up
7. query information in pgAdmin4 for example >> SELECT count(*) FROM ... 