from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os
import requests


# room setup
arduino_to_room = {
    "Clara": "1.29",
    "Alina": "2.06"
    }

def zeit():
    return datetime.now()

# logging because there won't be errors :D
def log(msg: str):
    log_path = "log.txt"
    with open(log_path, "a") as file:
        file.write(f"\n[PARSER] [{zeit()}]  "+msg)
    print(f"\n[PARSER] [{current_datetime}]  "+msg)

# webhook for easy discord access
webhook = "https://discord.com/api/webhooks/1387689544270217226/q-Ndkp2sMnJPHmFmNPmakhIPK12OibffHKmkEgsmmd9JEZl1csuQlt62BzTy3ipzpqHf"
# send alerts via discord to notify if error or just send some stuff (e.g. db)
def sende_discord_nachricht(text):
    content = {"content": f"\n[PARSER] [{zeit()}]  "+text}
    response = requests.post(webhook, json=content)
    if response.status_code != 204: #204 == our friend
        log(f"Fehler beim Senden der Discord-Nachricht: {response.status_code} - {response.text}")

# sends db to discord so that I can look at the new data from home :D
def sende_db_discord():
    payload = {"upload_file": open("instance/sensor_data.db", "rb")}
    response = requests.post(webhook, files=payload)
    if response.status_code != 204:
        log(f"Fehler beim Senden der DB über Discord: {response.status_code} - {response.text}")
        sende_discord_nachricht(f"Fehler beim Senden der DB über Discord: {response.status_code} - {response.text}")

# Setup stuff
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sensor_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # turn off unnecessary modification tracking

db = SQLAlchemy(app)

# db setup
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # db intern id
    arduino_id = db.Column(db.String(50), nullable=False)  # arduino id (Calra/Alina)
    sensor_type = db.Column(db.String(50), nullable=False)  # sensor type
    date = db.Column(db.Date, nullable=False)  # date
    time = db.Column(db.Time, nullable=False)  # time
    measurement_id = db.Column(db.String(50), nullable=False)  # measurement id
    value = db.Column(db.Float, nullable=False)  # value
    unit = db.Column(db.String(20), nullable=False)  # unit
    class_room = db.Column(db.String(50), nullable=False) # room
    log("setup database")

booli_the_boolean = False # booli is here to make sure a message won't get send twice

# Receive data 
@app.route("/sensor", methods=["POST"])
def receive_data():
    now = zeit().time()
    now = time(now.hour, now.minute)

    log(f"request to save data received from {request.remote_addr}")

    if now == time(5, 59) and !booli_the_boolean: # Cheduled reboot to prevent bugs due to long uptime stuff idk
        sende_discord_nachricht("Cheduled rebbot. Rebooting...")
        os.system("sudo reboot")
        booli_the_boolean = True
    elif now == time(13, 59)and !booli_the_boolean: # send message to let me now the server is still recieving new data
        sende_discord_nachricht("Cheduled update: still running and recieving data")
        booli_the_boolean = True
    elif now == time(17, 59)and !booli_the_boolean: # sends db with new data once per day
        sende_db_discord()
        sende_discord_nachricht("Cheduled data base sending ohhh yeah baby")
        booli_the_boolean = True
    else:
        booli_the_boolean = False

    data = request.get_json() 

    # unpack sent data and save to db
    try:
        for sensor_data in data:
            if sensor_data["value"] == 0: # send alert if the data sent is 0
                sende_discord_nachricht(f"Arduino {sensor_data["arduino_id"]}: {sensor_data["value"]}{sensor_data["unit"]} {sensor_data["sensor_type"]}")
            eintrag = SensorData(
                arduino_id=sensor_data["arduino_id"],
                sensor_type=sensor_data["sensor_type"],
                date=datetime.today().date(),
                time=now,
                measurement_id=sensor_data["measurement_id"],
                value=float(sensor_data["value"]),
                unit=sensor_data["unit"],
                class_room=arduino_to_room[sensor_data["arduino_id"]]
            )
            db.session.add(eintrag)

        db.session.commit()  # save data to db
        log("data saved to database")
        return jsonify({"status": "success"}), 201
    except Exception as e: # send alerts if error while saving to db
        log(f"Error: {e}")
        sende_discord_nachricht(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    log("starting...")
    sende_discord_nachricht("Starting...")
    # create db if not existent
    with app.app_context():
        db.create_all()
    # start server
    port_to_use = 5000
    host_to_use = "0.0.0.0"
    sende_discord_nachricht(f"host {host_to_use} is running on port {port_to_use}") # message when running
    log(f"host {host_to_use} is running on port {port_to_use}")
    app.run(host=host_to_use, port=port_to_use)
