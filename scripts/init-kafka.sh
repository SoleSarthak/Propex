#!/bin/bash

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
cub kafka-ready -b kafka:9092 1 30

# List of topics to create
TOPICS=("cve.raw" "dependency.resolved" "impact.scored" "notifications.out")

for topic in "${TOPICS[@]}"; do
  echo "Creating topic: $topic"
  kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1 --topic "$topic"
  
  echo "Creating DLQ for: $topic"
  kafka-topics --create --if-not-exists --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --topic "$topic.dlq"
done

echo "Kafka initialization complete."
