# Data Engineering System Project for gaming sales information

## Overview

1. Data ingestion that  load the csv file to the schema to transformation that read data from the landing schema, Build a star schema and load the tables to the staging schema for visualization.
2. Connect to the mysql database and send information from database to visualization in metabase.

## How to run this etl process

1. run make up : Create and run all the containers.
2. run make ci : Format, and run the tests.
3. run make etl : Run the pipeline.
4. run make warehouse : Connect to the Postgres database and check the data.
Go to localhost:3000 to open Metabase.
5. run make down : Stop the containers.
