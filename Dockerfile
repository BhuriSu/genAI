FROM apache/airflow:2.9.2 

USER root

RUN apt-get update && \
    apt-get -y install git && \
    apt-get clean

USER airflow
   
COPY requirements.txt /opt/airflow
WORKDIR /opt/airflow
RUN pip install -r requirements.txt 
