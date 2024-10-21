from flask import Flask, request, jsonify, render_template
import csv

# Global variables
app = Flask(__name__)  # Flask app instance
station_data = []


# Function to read station data from a CSV file
def load_stations_data(file_path):
    global station_data
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            station_data.append({
                "Station code": row['Station code'],
                "Station name": row['Station name(district)'],
                "Address": row['Address'],
                "Latitude": float(row['Latitude']),
                "Longitude": float(row['Longitude'])
            })
    print("Station data loaded successfully.")
    print(station_data)


# Endpoints
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/stations', methods=['GET'])
def get_stations():
    return jsonify(station_data)


@app.route('/data', methods=['POST'])
def receive_data():
    try:
        # Get JSON data from the request
        data = request.get_json()

        if not data:
            return jsonify({"message": "No JSON data received"}), 400

        # Print the received data to the console
        print("Received data:", data)

        # Return success response
        return jsonify({"message": "Data received successfully", "data": data}), 200

    except Exception as e:
        print(f"Error receiving data: {e}")
        return jsonify({"message": f"Error receiving data: {e}"}), 500


def main():
    # Load stations data (id, name, locations)
    file_path = './data/Measurement_station_info.csv'
    load_stations_data(file_path)
    # Run Flask server
    app.run(debug=True)


if __name__ == '__main__':
    main()
