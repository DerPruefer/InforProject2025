from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os
import requests


log_path = "log.txt"

classroom = "undefined"

booli_the_boolean1 = False
booli_the_boolean2 = False
booli_the_boolean3 = False

arduino_to_room = {
    "Clara": "1.14",
    "Alina": "2.06"
    }

WEBHOOK_URL = "https://discord.com/api/webhooks/1387689544270217226/q-Ndkp2sMnJPHmFmNPmakhIPK12OibffHKmkEgsmmd9JEZl1csuQlt62BzTy3ipzpqHf"
def sende_discord_nachricht(text):
    current_datetime = datetime.now()
    payload = {"content": f"\n[PARSER] [{current_datetime}]  "+text}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Fehler beim Senden der Discord-Nachricht: {response.status_code} - {response.text}")

def sende_db_discord():
    payload = {'upload_file': open('instance/sensor_data.db', 'rb')}
    response = requests.post(WEBHOOK_URL, files=payload)
    if response.status_code != 204:
        print(f"Fehler beim Senden der DB über Discord: {response.status_code} - {response.text}")


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
        if now >= time(5, 55) and now <= time(5, 57):
            if not booli_the_boolean1:
                sende_discord_nachricht("Cheduled rebbot. Rebooting...")
                booli_the_boolean1 = True
            os.system("sudo reboot")
        else:
            booli_the_boolean1 = False
        log(f"request rejected due to time restriction: {now}")
        return jsonify({"status": "error", "message": "Request only allowed between 06:00 and 19:00"}), 403

    if now >= time(13, 55) and now <= time(13, 57):
        if not booli_the_boolean2:
            sende_discord_nachricht("Cheduled update: still running and recieving data")
            booli_the_boolean2 = True
    else:
        booli_the_boolean2 = False

    if now >= time(17, 55) and now <= time(17, 57):
        if not booli_the_boolean3:
            sende_db_discord()
            sende_discord_nachricht("Cheduled data base sending ohhh yeah baby")
            booli_the_boolean3 = True
    else:
        booli_the_boolean3 = False

    data = request.get_json()

    try:
        for sensor_data in data:
            if sensor_data["value"] == 0:
                sende_discord_nachricht(f"0 Wert erkannt. Arduino {sensor_data['arduino_id']}")
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
        sende_discord_nachricht(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    log("starting...")
    sende_discord_nachricht("Starting...")
    # create db if not existent
    with app.app_context():
        db.create_all()
    # start server
    port_to_use = 5000
    host_to_use = "0.0.0.0"
    sende_discord_nachricht(f"host {host_to_use} is running on port {port_to_use}")
    log(f"host {host_to_use} is running on port {port_to_use}")
    app.run(host=host_to_use, port=port_to_use)
