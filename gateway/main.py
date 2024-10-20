import sys
import paho.mqtt.client as mqtt
import requests
import json


# Callback when a message is received from any MQTT topic the gateway is subscribed to
def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    # Forward data to Flask server in the cloud
    try:
        data = {"sensor_data": msg.payload.decode()}
        headers = {'Content-Type': 'application/json'}
        json_data = json.dumps(data)
        # response = requests.post(FLASK_SERVER_URL, data=json_data, headers=headers)
        #
        # if response.status_code == 200:
        #     print("Data successfully sent to the Flask server.")
        # else:
        #     print(f"Failed to send data to the Flask server: {response.status_code}")
    except Exception as e:
        print(f"Error forwarding data to Flask server: {e}")


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
    station_id = sys.argv[1]

    # Flask server details (on the cloud)
    # FLASK_SERVER_URL = "http://your-flask-server.com/api/data"
    FLASK_SERVER_URL = '127.0.0.1:5000'

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
