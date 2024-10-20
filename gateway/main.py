import sys
import paho.mqtt.client as mqtt
import requests
import json

station_id = None
FLASK_SERVER_URL = 'http://localhost:5000/data'
#expected_sensors = ['SO2', 'NO2', 'CO', 'O3', 'PM10', 'PM2.5']
expected_sensors = ['SO2', 'NO2']
sensors_data_buffer = {}


def check_buffer_full():
    keys = sensors_data_buffer.keys()
    if len(keys) != len(expected_sensors):
        return False
    return True


# Forward data to Flask server in the cloud
def forward_data():
    try:
        data = {
            'station_id': station_id,
            'sensor_data': sensors_data_buffer
        }
        headers = {'Content-Type': 'application/json'}
        json_data = json.dumps(data)
        response = requests.post(FLASK_SERVER_URL, data=json_data, headers=headers)

        if response.status_code == 200:
            print("Data successfully sent to the Flask server.")
        else:
            print(f"Failed to send data to the Flask server: {response.status_code}")
    except Exception as e:
        print(f"Error forwarding data to Flask server: {e}")


# Callback when a message is received from any MQTT topic the gateway is subscribed to
def on_message(client, userdata, msg):
    json_payload = msg.payload.decode()
    print(f"Received message on topic {msg.topic}: {json_payload}")

    dict_payload = json.loads(json_payload)

    # Extract the data in the payload
    sensor_type = dict_payload['sensor_type']
    timestamp = dict_payload['timestamp']
    value = dict_payload['value']

    # Change the format of the data
    sensor_data = {
        'timestamp': timestamp,
        'value': value
    }
    # Save the data in the buffer
    sensors_data_buffer[sensor_type] = sensor_data

    # Check if all sensors have sent the data
    if check_buffer_full():
        forward_data()
        sensors_data_buffer.clear()


# Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")


def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with return code {rc}")


'''
Granted_qos refers to the Quality of Service (QoS) level that the broker has granted for the subscription
to a specific topic. When an MQTT client subscribes to a topic,
it can request a certain QoS level (0, 1, or 2), but the broker may grant a different QoS level,
depending on its capabilities and policies

MID (Message Identifier)
'''


def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscription granted with QoS: {granted_qos}")


def main():
    # Read command line arguments
    if len(sys.argv) != 2:
        print("Usage: python script.py <station_id>")
        sys.exit(1)

    global station_id
    station_id = sys.argv[1]

    # MQTT broker details (local broker on the gateway)
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_TOPIC = f"station_{station_id}"
    MQTT_KEEPALIVE = 60

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_message = on_message
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

    # Start MQTT client
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
    mqtt_client.subscribe(MQTT_TOPIC)
    mqtt_client.loop_forever()


if __name__ == "__main__":
    main()
