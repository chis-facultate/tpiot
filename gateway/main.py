import sys
import paho.mqtt.client as mqtt
import requests
import json

station_code = None
flask_server_url = 'https://tpiot-1.onrender.com/data'
# flask_server_url = 'http://localhost:5000/data'
expected_sensors = ['SO2', 'NO2', 'CO', 'O3', 'PM10', 'PM2.5']
# expected_sensors = ['SO2', 'NO2']
sensors_data_buffer = {}


def check_buffer_full():
    keys = sensors_data_buffer.keys()
    if len(keys) != len(expected_sensors):
        return False
    return True


# Forward data to Flask server in the cloud
def forward_data():
    try:
        station_data = {
            'Station code': station_code,
            'Sensors data': sensors_data_buffer
        }
        headers = {'Content-Type': 'application/json'}
        json_station_data = json.dumps(station_data)  # Convert to JSON
        response = requests.post(flask_server_url, data=json_station_data, headers=headers)

        print('Sent data', json_station_data)
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
    item_name = dict_payload['Item name']
    value = dict_payload['Value']
    measurement_unit = dict_payload['Measurement unit']
    measurement_date = dict_payload['Measurement date']

    # Change the format of the data
    sensor_data = {
        'Value': value,
        'Measurement unit': measurement_unit,
        'Measurement date': measurement_date
    }
    # Save the data in the buffer
    sensors_data_buffer[item_name] = sensor_data

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

    global station_code
    station_code = sys.argv[1]

    # MQTT broker details (local broker on the gateway)
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_TOPIC = f"station_{station_code}"
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
