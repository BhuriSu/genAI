#!/usr/bin/env bash

set -e
source .venv/bin/activate  # Updated to use the virtual environment in the project root
python bash_script/dataframe_to_kafka.py -i datasets/thailand_tourist.csv -t office_input -rst 2
