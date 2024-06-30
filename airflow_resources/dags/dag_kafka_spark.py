import csv
import os
from datetime import timedelta, datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
# from airflow.operators.dummy import DummyOperator
# from airflow.operators.bash import BashOperator
# from airflow.decorators import task
# from cuallee import Check, CheckLevel
# import polars as pl


from src.kafka_client.kafka_stream_data import stream


start_date = datetime.today() - timedelta(days=1)


default_args = {
    "owner": "airflow",
    "start_date": start_date,
    "retries": 1,  # number of retries before failing the task
    "retry_delay": timedelta(seconds=5),
}


with DAG(
    dag_id="kafka_spark_dag",
    default_args=default_args,
    description='A simple DAG to fetch data \
    from corporation_financial and write to a file \
    and load france open data into database postgresql',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:
    
    # file_path = f'{os.getenv("AIRFLOW_HOME")}/data/corporation_financial.csv'


    kafka_stream_task = PythonOperator(
        task_id="kafka_data_stream",
        python_callable=stream,
        dag=dag,
    )

    spark_stream_task = DockerOperator(
        task_id="pyspark_consumer",
        image="rappel-conso/spark:latest",
        api_version="auto",
        auto_remove=True,
        command="./bin/spark-submit --master local[*] --packages org.postgresql:postgresql:42.5.4,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 ./spark_streaming.py",
        docker_url='tcp://docker-proxy:2375',
        environment={'SPARK_LOCAL_HOSTNAME': 'localhost'},
        network_mode="airflow-kafka",
        dag=dag,
    )
    
    # @task
    # def corporation_financial_exchanges(file_path):
    #     exchanges = []
    #     if exchanges:
    #         with open(file_path, 'w') as f:
    #             dict_reader = csv.DictReader(f)
    #             for row in dict_reader:
    #                 exchanges.append(row)
    #         return exchanges
                

    # def check_completeness(pl_df, column_name):
    #     check = Check(CheckLevel.ERROR, "Completeness")
    #     validation_results_df = (
    #         check.is_complete(column_name).validate(pl_df)
    #     )
    #     return validation_results_df["status"].to_list()
    
    # @task.branch
    # def check_data_quality(validation_results):
    #     if "FAIL" not in validation_results:
    #         return ['generate_dashboard']
    #     return ['stop_pipeline']
    
    # check_data_quality_instance = check_data_quality(check_completeness(pl.read_csv(file_path), "name"))

    # stop_pipeline = DummyOperator(task_id='stop_pipeline')

    # markdown_path = f'{os.getenv("AIRFLOW_HOME")}/visualization/'
    # q_cmd = (
    #     f'cd {markdown_path} && quarto render {markdown_path}/dashboard.qmd'
    # )
    # gen_dashboard = BashOperator(
    #     task_id="generate_dashboard", bash_command=q_cmd
    # )

    # corporation_financial_exchanges(file_path) >> check_data_quality_instance >> gen_dashboard
    # check_data_quality_instance >> stop_pipeline

    kafka_stream_task >> spark_stream_task