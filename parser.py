from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

log_path = "log.txt"

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
    sensorid = db.Column(db.String(50), nullable=False)  # sensor id
    sensortyp = db.Column(db.String(50), nullable=False)  # sensor type
    date = db.Column(db.Date, nullable=False)  # date
    time = db.Column(db.Time, nullable=False)  # time
    messungid = db.Column(db.String(50), nullable=False)  # measurement id
    wert = db.Column(db.Float, nullable=False)  # value
    einheit = db.Column(db.String(20), nullable=False)  # unit
    log("setup database")


# API-Route für das Empfangen von Sensordaten
@app.route('/sensor', methods=['POST'])
def receive_data():
    log(f"request received from {request.remote_addr}")
    data = request.get_json()

    try:
        for sensor_data in data:
            eintrag = SensorData(
                sensorid=sensor_data['sensorid'],
                sensortyp=sensor_data['sensortyp'],
                date=datetime.strptime(sensor_data['date'], '%Y-%m-%d').date(),  # Datum im richtigen Format umwandeln
                time=datetime.strptime(sensor_data['time'], '%H:%M:%S').time(),  # Zeit im richtigen Format umwandeln
                messungid=sensor_data['messungid'],
                wert=float(sensor_data['wert']),
                einheit=sensor_data['einheit']
            )
            db.session.add(eintrag)

        db.session.commit()  # save data to db
        log("data saved to datbase")
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
