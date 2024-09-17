#!/usr/bin/env bash

set -e
source .venv/bin/activate  # Updated to use the virtual environment in the project root
python spark_streaming/spark_to_minio.py
