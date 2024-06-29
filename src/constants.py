import os

# API params
PATH_LAST_PROCESSED = "./data/last_processed.json"
MAX_LIMIT = 100

# We have three parameters in the URL:
# 1. MAX_LIMIT: the maximum number of records to be returned by the API
# 2. date_de_publication: the date from which we want to get the data

URL_API = "https://api.openbrewerydb.org/v1/breweri?limit={}"
URL_API = URL_API.format(MAX_LIMIT, "{}")

# POSTGRES PARAMS
user_name = os.getenv("POSTGRES_DOCKER_USER", "localhost")
POSTGRES_URL = f"jdbc:postgresql://{user_name}:5432/postgres"
POSTGRES_PROPERTIES = {
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD"),
    "driver": "org.postgresql.Driver",
}

NEW_COLUMNS = [
    "id",
    "name",
    "state",
    "city",
    "brewery_type",
]

DB_FIELDS =  NEW_COLUMNS
