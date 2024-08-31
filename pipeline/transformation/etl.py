import logging

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def read_table(engine, table_name):
    """read data from the landing schema"""
    try:
        df = pd.read_sql_query(
            f'SELECT * FROM landing_area."{table_name}"', engine
        )
        logger.info('Table read from the landing_area!!!!')
        return df
    except Exception as e:
        logger.error('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        logger.error(f'Enable to read data from landing_area: {e}')


def clean_data(df):
    # data cleaning
    df['Name'] = df['Name'].fillna("NO Name")
    df['Platform'] = df['Platform'].fillna("NO Platform")
    df['EU_Sales'] = df['EU_Sales'].fillna(-1) #This method is used to fill any NaN (Not a Number) 
    df['NA_Sales'] = df['NA_Sales'].fillna(-1)
    df['JP_Sales'] = df['JP_Sales'].fillna(-1)
    df['Global_Sales'] = df['Global_Sales'].fillna(-1)

    return df


def create_schema(df):
    """Build a star schema"""

    name_df = df[['Name']]
    name_df = name_df.drop_duplicates()
    name_df = name_df.reset_index(drop=True)
    name_df = name_df.reset_index(names="Name_ID")
    name_df["Name_ID"] += 1

    platform_df = df[['Platform']]
    platform_df = platform_df.reset_index(drop=True)
    platform_df = platform_df.reset_index(names="Platform_ID")
    platform_df["Platform_ID"] += 1

    eu_sales_df = df[['EU_Sales']]
    eu_sales_df = eu_sales_df.reset_index(drop=True)
    eu_sales_df = eu_sales_df.reset_index(names="EU_Sales_ID")
    eu_sales_df["EU_Sales_ID"] += 1

    na_sales_df = df[['NA_Sales']]
    na_sales_df = na_sales_df.reset_index(drop=True)
    na_sales_df = na_sales_df.reset_index(names="NA_Sales_ID")
    na_sales_df["NA_Sales_ID"] += 1

    jp_sales_df = df[['JP_Sales']]
    jp_sales_df = jp_sales_df.reset_index(drop=True)
    jp_sales_df = jp_sales_df.reset_index(names="JP_Sales_ID")
    jp_sales_df["JP_Sales_ID"] += 1

    global_sales_df = df[['Global_Sales']]
    global_sales_df = global_sales_df.reset_index(drop=True)
    global_sales_df = global_sales_df.reset_index(names="Global_Sales_ID")
    global_sales_df["Global_Sales_ID"] += 1

    fact_table = (
        df.merge(name_df, on='Name')
        .merge(platform_df, on='Platform')
        .merge(eu_sales_df, on='EU_Sales')
        .merge(na_sales_df, on='NA_Sales')
        .merge(jp_sales_df, on='JP_Sales')
        .merge(global_sales_df, on='Global_Sales')
    )

    fact_table = fact_table.drop_duplicates()

    return {
        "Name": name_df.to_dict(orient="dict"),
        "Platform": platform_df.to_dict(orient="dict"),
        "EU_Sales": eu_sales_df.to_dict(orient="dict"),
        "NA_Sales": na_sales_df.to_dict(orient="dict"),
        "JP_Sales": jp_sales_df.to_dict(orient="dict"),
        "Global_Sales": global_sales_df.to_dict(orient="dict"),
        "Fact_table": fact_table.to_dict(orient="dict"),
    }


def load_tables_staging(dict, engine):
    """load the tables to the staging schema for visualization"""
    try:
        for df_name, value_dict in dict.items():
            value_df = pd.DataFrame(value_dict)
            logger.info(
                f'Importing {len(value_df)} rows from'
                f'landing_area to staging_area.{df_name}'
            )
            value_df.to_sql(
                df_name,
                engine,
                if_exists='replace',
                index=False,
                schema='staging_area',
            )

            logger.info('!!!!!!!!')
            logger.info(f'Table {df_name} loaded successfully')

    except Exception as e:
        logger.error("!!!!!!!!!!!!!!!!!!!!!!")
        logger.error(f"Enable to load the data to staging area : {e}")