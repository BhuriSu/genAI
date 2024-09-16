from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(
    bootstrap_servers=['localhost:9092'], #This is the host and port Kafka runs.
    client_id='kafka_admin_client'
)
topic_list = admin_client.list_topics()
def create_new_topic():
    """Checks if the topic tourist_input exists or not. If not, creates the topic."""
    try:
        admin_client.create_topics(new_topics=[NewTopic('tourist_input', 1, 1)])  # The first number is partitions for the topic and A replication factor of 1 means no replication
        return "Topic tourist_input successfully created"
    except:
        return "Topic tourist_input already exists"

if __name__ == "__main__":
    create_new_topic()