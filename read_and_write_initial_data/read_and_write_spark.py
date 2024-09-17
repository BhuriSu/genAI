
import findspark
from functools import reduce
from pyspark.sql import DataFrame
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *

findspark.init("/opt/manual/spark")  # Initialize Spark

# Create Spark session
spark = SparkSession.builder \
    .appName("Thailand Tourist Data Processing") \
    .master("local[2]") \
    .getOrCreate()

# Define the columns to keep
columns = ['date', 'province_eng', 'region_eng', 'value']

# File path to the dataset
file_path = 'datasets/thailand_tourist.csv'

def create_separate_dataframes(file_path: str) -> dict:
    """
    Creates separate dataframes for each year from the dataset.
    """
    # Read the CSV file with only the necessary columns
    df = spark.read.csv(file_path, header=True, inferSchema=True).select(columns)

    # Convert 'date' column to date format
    df = df.withColumn('date', F.to_date(F.col('date')))

    # List of years to separate
    years = ['2019', '2020', '2021', '2022', '2023']

    # Dictionary to store dataframes by year
    dataframes_by_year = {}

    # Loop through each year and create a separate dataframe
    for year in years:
        # Filter data by the year
        df_year = df.filter(F.year(F.col('date')) == int(year))
        # Group by province_eng and region_eng, then sum the 'value'
        df_grouped = df_year.groupBy('province_eng', 'region_eng').agg(F.sum('value').alias('value'))
        # Add the dataframe to the dictionary
        dataframes_by_year[year] = df_grouped

    return dataframes_by_year


def union_all(dfs: list) -> DataFrame:
    """
    Union multiple DataFrames into a single DataFrame.
    """
    return reduce(DataFrame.unionAll, dfs)


def create_main_dataframe(separate_dataframes: dict) -> DataFrame:
    """
    Concatenates year-separated dataframes and adds a 'year' column.
    """
    # Add 'year' column to each dataframe and collect them into a list
    dfs_with_year = []
    for year, df in separate_dataframes.items():
        df_with_year = df.withColumn('year', F.lit(year))
        dfs_with_year.append(df_with_year)

    # Concatenate all dataframes
    main_df = union_all(dfs_with_year)

    # Sort by year
    main_df = main_df.orderBy('year')

    return main_df


def write_main_dataframe(df: DataFrame, output_path: str):
    """
    Writes the final dataframe to a CSV file.
    """
    df.write.csv(output_path, header=True, mode='overwrite')
    print(f"Data has been written to {output_path}")


if __name__ == '__main__':
    # Create separate dataframes by year
    all_dataframes = create_separate_dataframes(file_path)

    # Create the main dataframe by concatenating year-based dataframes
    main_dataframe = create_main_dataframe(all_dataframes)

    # Define the output path
    output_path = 'datasets/thailand_tourist_grouped.csv'

    # Write the final dataframe to a CSV file
    write_main_dataframe(main_dataframe, output_path)
