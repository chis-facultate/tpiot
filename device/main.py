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
def publish_data(data, mqtt_client, mqtt_topic):
    try:
        # Convert the data to JSON format
        data_json = json.dumps(data)

        # Publish the data to the specified MQTT topic
        mqtt_client.publish(mqtt_topic, data_json)
        print(f"Published data: {data_json}")

    except Exception as e:
        print(f"Failed to publish data: {e}")


# Function to simulate reading data and sending it via MQTT
def simulate_sensor_data(station_id, item_code, mqtt_client, mqtt_topic):
    file_path = f"../data/station_{station_id}/station_{station_id}_item_{item_code}.csv"

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        sys.exit(1)

    sensor_data = read_sensor_data(file_path)

    item_dict = {
        '1': {
            'Item name': 'SO2',
            'Unit of measurement': 'ppm'
              },
        '3': {
            'Item name': 'NO2',
            'Unit of measurement': 'ppm'
              },
        '5': {
            'Item name': 'CO',
            'Unit of measurement': 'ppm'
              },
        '6': {
            'Item name': 'O3',
            'Unit of measurement': 'ppm'
              },
        '8': {
            'Item name': 'PM10',
            'Unit of measurement': 'mcg/m3'
              },
        '9': {
            'Item name': 'PM2.5',
            'Unit of measurement': 'mcg/m3'
              }
    }

    item_name = item_dict[item_code]['Item name']
    measurement_unit = item_dict[item_code]['Unit of measurement']

    if sensor_data is not None:
        # Loop through each row of sensor data
        for index, row in sensor_data.iterrows():
            # Create a dictionary with the timestamp and value (simulate sensor data)
            data = {
                'Item name': item_name,
                'Value': row['Average value'],
                'Measurement unit': measurement_unit,
                'Measurement date': row['Measurement date']
            }

            # Publish the data to the MQTT broker
            publish_data(data, mqtt_client, mqtt_topic)

            # Simulate a delay between sensor readings
            time.sleep(20)
    else:
        print('End of file')


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <station_code> <item_code>")
        sys.exit(1)

    # Read command line arguments
    station_code = sys.argv[1]
    item_code = sys.argv[2]

    # MQTT broker details
    mqtt_broker = '127.0.0.1'
    mqtt_port = 1883
    mqtt_topic = f'station_{station_code}'
    mqtt_keepalive = 60

    # Initialize MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish = on_publish
    # Enable automatic reconnection
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

    # Connect to the MQTT broker
    try:
        mqtt_client.connect(mqtt_broker, mqtt_port, mqtt_keepalive)
        print(f"Connected to MQTT broker at {mqtt_broker}")
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        return

    # Simulate sending sensor data to the MQTT broker
    simulate_sensor_data(station_code, item_code, mqtt_client, mqtt_topic)

    # Disconnect from the MQTT broker
    mqtt_client.disconnect()
    print("Disconnected from MQTT broker.")


if __name__ == '__main__':
    main()
