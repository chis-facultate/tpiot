import pandas as pd
import time
import json
import paho.mqtt.client as mqtt
import os
import sys


# Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        # Optionally subscribe to topics here if needed
    else:
        print(f"Failed to connect, return code {rc}")


def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with return code {rc}")


def on_publish(client, userdata, mid):
    print(f"Message {mid} published")


# Function to read sensor data from the CSV file
def read_sensor_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except Exception as e:
        print(f"Error reading sensor data file: {e}")
        return None


# Function to publish data to the MQTT broker
def publish_data(data, mqtt_client, MQTT_TOPIC):
    try:
        # Convert the data to JSON format
        data_json = json.dumps(data)

        # Publish the data to the specified MQTT topic
        mqtt_client.publish(MQTT_TOPIC, data_json)
        print(f"Published data: {data_json}")

    except Exception as e:
        print(f"Failed to publish data: {e}")


# Function to simulate reading data and sending it via MQTT
def simulate_sensor_data(station_id, item_id, mqtt_client, MQTT_TOPIC):
    file_path = f"../data/station_{station_id}/station_{station_id}_item_{item_id}.csv"

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    sensor_data = read_sensor_data(file_path)

    item_dict = {
        '1': 'SO2',
        '3': 'NO2',
        '5': 'CO',
        '6': 'O3',
        '8': 'PM10',
        '9': 'PM2.5'
    }

    sensor_type = item_dict[item_id]

    if sensor_data is not None:
        # Loop through each row of sensor data
        for index, row in sensor_data.iterrows():
            # Create a dictionary with the timestamp and value (simulate sensor data)
            data = {
                'sensor_type': sensor_type,
                'timestamp': row['Measurement date'],
                'value': row['Average value']
            }

            # Publish the data to the MQTT broker
            publish_data(data, mqtt_client, MQTT_TOPIC)

            # Simulate a delay between sensor readings
            time.sleep(10)


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <station_id> <item_id>")
        sys.exit(1)

    # Read command line arguments
    station_id = sys.argv[1]
    item_id = sys.argv[2]

    # MQTT broker details
    MQTT_BROKER = "127.0.0.1"
    MQTT_PORT = 1883
    MQTT_TOPIC = f"station_{station_id}"
    MQTT_KEEPALIVE = 60

    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish = on_publish
    # Enable automatic reconnection
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

    # Connect to the MQTT broker
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        return

    # Simulate sending sensor data to the MQTT broker
    simulate_sensor_data(station_id, item_id, mqtt_client, MQTT_TOPIC)

    # Disconnect from the MQTT broker
    mqtt_client.disconnect()
    print("Disconnected from MQTT broker.")


if __name__ == "__main__":
    main()
