from pyspark.sql import SparkSession
from pyspark.sql.functions import (col)
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType
import logging
import sys 

sys.path.append('./')
from validate import df_count, df_print_schema, df_top10_rec

# create spark session state
def spark_session():
    appName = "spark etl pipeline"
    spark = SparkSession.builder \
        .appName(appName) \
        .getOrCreate()
    return spark

def load_corporation_table(spark, file_dir, file_format):
    try:
        logging.info("load_corporation_file() is Started ...")
        df = spark. \
                read. \
                format(file_format). \
                options(header=True). \
                options(inferSchema=True). \
                options(delimiter=','). \
                load(file_dir)
    except Exception as e:
        logging.error("Error in the method - load_table()). Please check the Stack Trace. " + str(e))
        raise
    else:
        logging.info(f"The input File {file_dir} is loaded to the data frame. The load_corporation_table() Function is completed.")
    return df

@udf(returnType=IntegerType())
def column_split_cnt(column):
    return len(column.split(' '))

def perform_data_clean(df1):
    ### Clean df_corporation DataFrame:
    #1 Select only required Columns
    try:
        logging.info(f"perform_data_clean() is started for df_corporation dataframe...")
        df_corporation_info = df1.select(
                                 df1.Symbol,
                                 df1.Name,
                                 df1.Sector,
                                 df1.PricePerEarnings,
                                 df1.EarningsPerShare,
                                 df1.DividendYield,
                                 df1.MarketCap
                                 )
    except Exception as exp:
        print(exp)
        raise
    else:
        logging.info("perform_data_clean() is completed...")
    return df_corporation_info

def price_per_earning_report(df_corporation_info):
    try:
        logging.info("Transform - pe_report() is started...")
        df_corporation_pe = df_corporation_info.orderBy(col("PricePerEarnings").desc())
        df_corporation_pe.toPandas().to_csv('/opt/airflow/staging/corporation-financial.csv', index=False)
    except Exception as exp:
        logging.error("Error in the method - pe_report(). Please check the Stack Trace. " + str(exp), exc_info=True)
        raise
    else:
        logging.info("Transform - pe_report() is completed...")
    return df_corporation_pe

def earning_per_share_report(df_corporation_info):
    try:
        logging.info("Transform - eps_report() is started...")
        df_corporation_eps = df_corporation_info.orderBy(col("EarningsPerShare").desc())
        df_corporation_eps.toPandas().to_csv('/opt/airflow/staging/corporation-financial.csv', index=False)
    except Exception as exp:
        logging.error("Error in the method - eps_report(). Please check the Stack Trace. " + str(exp), exc_info=True)
        raise
    else:
        logging.info("Transform - eps_report() is completed...")
    return df_corporation_eps

def market_cap_report(df_corporation_info):
    try:
        logging.info("Transform - marketcap_report() is started...")
        df_corporation_mc = df_corporation_info.orderBy(col("MarketCap").desc())
        df_corporation_mc.toPandas().to_csv('/opt/airflow/staging/corporation-financial.csv', index=False)
    except Exception as exp:
        logging.error("Error in the method - marketcap_report(). Please check the Stack Trace. " + str(exp), exc_info=True)
        raise
    else:
        logging.info("Transform - marketcap_report() is completed...")
    return df_corporation_mc

def dividend_yield_report(df_corporation_info):
    try:
        logging.info("Transform - dividend_yield_report() is started...")
        df_corporation_dy = df_corporation_info.orderBy(col("DividendYield").desc())
        df_corporation_dy.toPandas().to_csv('/opt/airflow/staging/corporation-financial.csv', index=False)
    except Exception as exp:
        logging.error("Error in the method - dividend_yield_report(). Please check the Stack Trace. " + str(exp), exc_info=True)
        raise
    else:
        logging.info("Transform - dividend_yield_report() is completed...")
    return df_corporation_dy

def main():
    """base function that runs spark etl"""
    try:
        spark = spark_session()
    
        corporation_financial_dir = '/opt/airflow/corporation-financial.csv'
       
        #file_dir = '/opt/airflow/data'
        df_corporation = load_corporation_table(spark = spark, file_dir = corporation_financial_dir, file_format = 'csv')

        df_count(df_corporation,'df_corporation')
        ### Initiate corporation_run_data_preprocessing Script
            ## Perform data Cleaning Operations for df_corporation
        df_corporation_sel = perform_data_clean(df_corporation)
        #Validation for df_corporation    
        df_print_schema(df_corporation,'df_corporation')
        ### Initiate corporation_run_data_transform Script and write output to local staging dir
        df_corporation_pe = price_per_earning_report(df_corporation_sel)
        df_corporation_eps = earning_per_share_report(df_corporation_sel)
        df_corporation_mc = market_cap_report(df_corporation_sel)
        df_corporation_dy = dividend_yield_report(df_corporation_sel)
        
        df_print_schema(df_corporation_pe,'df_corporation_pe')
        df_count(df_corporation_pe,'df_corporation_pe')

        df_print_schema(df_corporation_eps,'df_corporation_eps')
        df_count(df_corporation_eps,'df_corporation_eps')

        df_print_schema(df_corporation_mc,'df_corporation_mc')
        df_count(df_corporation_mc,'df_corporation_mc')

        df_print_schema(df_corporation_dy,'df_corporation_dy')
        df_count(df_corporation_dy,'df_corporation_dy')
 

    except Exception as exp:
            logging.error("Error Occurred in the main() method. check the Stack Trace to go to the respective module "
                "and fix it." + str(exp))
            sys.exit(1)


if __name__ == "__main__" :
    logging.info("spark_etl is Started ...")
    main()
