from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import os

class PostgresETL:
    def __init__(self, db_config: Dict):
        """
        Initialize ETL system with database configuration
        
        db_config = {
            'host': 'localhost',
            'database': 'your_db',
            'user': 'your_user',
            'password': 'your_password',
            'port': '5432'
        }
        """
        self.db_config = db_config
        self.spark = self._initialize_spark()
        self._setup_logging()
        
    def _initialize_spark(self) -> SparkSession:
        """Initialize Spark with PostgreSQL JDBC driver"""
        return SparkSession.builder \
            .appName("PostgreSQL ETL") \
            .config("spark.driver.memory", "16g") \
            .config("spark.executor.memory", "32g") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.jars", "postgresql-42.2.23.jar") \
            .getOrCreate()
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_jdbc_url(self) -> str:
        """Create JDBC URL for PostgreSQL connection"""
        return f"jdbc:postgresql://{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
    
    def extract_from_postgres(self, query: str, partition_column: str = None, num_partitions: int = None):
        """
        Extract data from PostgreSQL using Spark JDBC
        Supports partitioned reads for large datasets
        """
        try:
            jdbc_url = self._get_jdbc_url()
            
            read_options = {
                "url": jdbc_url,
                "driver": "org.postgresql.Driver",
                "user": self.db_config['user'],
                "password": self.db_config['password'],
                "query": query
            }
            
            # Add partitioning for large datasets
            if partition_column and num_partitions:
                read_options.update({
                    "partitionColumn": partition_column,
                    "lowerBound": "1",  # Adjust based on your data
                    "upperBound": str(num_partitions * 10000),  # Adjust based on your data
                    "numPartitions": str(num_partitions)
                })
            
            return self.spark.read \
                .format("jdbc") \
                .options(**read_options) \
                .load()
                
        except Exception as e:
            self.logger.error(f"Error extracting data: {e}")
            raise

    def transform_data(self, df, transformations: List[Dict]):
        """
        Apply a series of transformations to the dataframe
        
        transformations = [
            {
                'type': 'select',
                'columns': ['col1', 'col2']
            },
            {
                'type': 'filter',
                'condition': 'col1 > 100'
            },
            {
                'type': 'groupby',
                'columns': ['col1'],
                'aggs': [{'col': 'col2', 'func': 'sum'}]
            }
        ]
        """
        try:
            for t in transformations:
                if t['type'] == 'select':
                    df = df.select(t['columns'])
                elif t['type'] == 'filter':
                    df = df.filter(t['condition'])
                elif t['type'] == 'groupby':
                    group_cols = t['columns']
                    aggs = [expr(f"{agg['func']}({agg['col']})").alias(f"{agg['col']}_{agg['func']}")
                           for agg in t['aggs']]
                    df = df.groupBy(group_cols).agg(*aggs)
                elif t['type'] == 'window':
                    window_spec = Window.partitionBy(t['partition_by']).orderBy(t['order_by'])
                    df = df.withColumn(t['new_column'], 
                                     expr(t['function']).over(window_spec))
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            raise

    def load_to_postgres(self, df, table_name: str, write_mode: str = "append"):
        """Load data to PostgreSQL using JDBC"""
        try:
            jdbc_url = self._get_jdbc_url()
            
            df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("driver", "org.postgresql.Driver") \
                .option("dbtable", table_name) \
                .option("user", self.db_config['user']) \
                .option("password", self.db_config['password']) \
                .mode(write_mode) \
                .save()
                
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise

    def run_etl_job(self, extract_query: str, transformations: List[Dict], 
                    target_table: str, partition_column: str = None, 
                    num_partitions: int = None):
        """Run complete ETL job"""
        try:
            # Extract
            self.logger.info("Starting data extraction...")
            df = self.extract_from_postgres(extract_query, partition_column, num_partitions)
            
            # Transform
            self.logger.info("Applying transformations...")
            df_transformed = self.transform_data(df, transformations)
            
            # Load
            self.logger.info("Loading data to target table...")
            self.load_to_postgres(df_transformed, target_table)
            
            self.logger.info("ETL job completed successfully!")
            
        except Exception as e:
            self.logger.error(f"ETL job failed: {e}")
            raise
        finally:
            self.spark.catalog.clearCache()

# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'your_db',
        'user': 'your_user',
        'password': 'your_password',
        'port': '5432'
    }
    
    # Initialize ETL
    etl = PostgresETL(db_config)
    
    # Define ETL job
    extract_query = """
        SELECT id, product_name, category, price, quantity
        FROM sales_data
        WHERE date >= '2024-01-01'
    """
    
    transformations = [
        {
            'type': 'groupby',
            'columns': ['category'],
            'aggs': [
                {'col': 'price', 'func': 'sum'},
                {'col': 'quantity', 'func': 'sum'}
            ]
        }
    ]
    
    # Run ETL job
    etl.run_etl_job(
        extract_query=extract_query,
        transformations=transformations,
        target_table='sales_summary',
        partition_column='id',
        num_partitions=10
    )