from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os


log_path = "log.txt"

classroom = "undefined"

arduino_to_room = {
    "Clara": "undefined",
    "Alina": "undefined"
    }

def log(msg: str):
    current_datetime = datetime.now()
    with open(log_path, "a") as file:
        file.write(f"\n[PARSER] [{current_datetime}]  "+msg)
    print(f"\n[PARSER] [{current_datetime}]  "+msg)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # turn off unnecessary modification tracking

db = SQLAlchemy(app)


# db setup
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # db intern id
    arduino_id = db.Column(db.String(50), nullable=False)  # arduino id
    sensor_type = db.Column(db.String(50), nullable=False)  # sensor type
    date = db.Column(db.Date, nullable=False)  # date
    time = db.Column(db.Time, nullable=False)  # time
    measurement_id = db.Column(db.String(50), nullable=False)  # measurement id
    value = db.Column(db.Float, nullable=False)  # value
    unit = db.Column(db.String(20), nullable=False)  # unit
    class_room = db.Column(db.String(50), nullable=False)
    log("setup database")



@app.route('/sensor', methods=['POST'])
def receive_data():
    now = datetime.now().time()
    start_time = time(6, 0)   # 06:00 Uhr
    end_time = time(19, 0)    # 19:00 Uhr

    log(f"request to save data received from {request.remote_addr}")

    if not (start_time <= now <= end_time):
        log(f"request rejected due to time restriction: {now}")
        return jsonify({"status": "error", "message": "Request only allowed between 06:00 and 19:00"}), 403

    data = request.get_json()

    try:
        for sensor_data in data:
            eintrag = SensorData(
                arduino_id=sensor_data['arduino_id'],
                sensor_type=sensor_data['sensor_type'],
                date=datetime.today().date(),
                time=now,
                measurement_id=sensor_data['measurement_id'],
                value=float(sensor_data['value']),
                unit=sensor_data['unit'],
                class_room=arduino_to_room[sensor_data['arduino_id']]
            )
            db.session.add(eintrag)

        db.session.commit()  # save data to db
        log("data saved to database")
        return jsonify({"status": "success"}), 201
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

# API-route for room setup
@app.route('/terminate', methods=['POST'])
def terminate():
    log(f"request to terminate from {request.remote_addr}")

    try:
        os._exit(0)
        return jsonify({"status": "success"}), 201
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/reboot', methods=['POST'])
def reboot():
    log(f"request to reboot received from {request.remote_addr}")

    try:
        os.system("sudo reboot")
        return jsonify({"status": "success"}), 201
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


# API-route for room setup
@app.route('/room', methods=['POST'])
def setup_room():
    log(f"request to change room received from {request.remote_addr}")
    data = request.data.decode("utf-8")

    try:
        data= data.split(" ")
        log(str(data))
        arduino_to_room[data[0]] = data[1]
        log(f"changed room for {data[0]} to {data[1]}")
        return jsonify({"status": "success"}), 201
    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    log("starting...")
    # create db if not existent
    with app.app_context():
        db.create_all()
    # start server
    port_to_use = 5000
    host_to_use = "0.0.0.0"
    app.run(host=host_to_use, port=port_to_use)
    log(f"host {host_to_use} is running on port {port_to_use}")
