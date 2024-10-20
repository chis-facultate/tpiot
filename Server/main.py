from flask import Flask, request, jsonify

# Create a Flask app instance
app = Flask(__name__)


# Endpoints
@app.route('/', methods=['GET'])
def home():
    return "Hello, World!"


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


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
