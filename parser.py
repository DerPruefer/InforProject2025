from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sensor_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Deaktiviert unnötige Modifikations-Tracking

# Initialisiere SQLAlchemy mit der Flask-Anwendung
db = SQLAlchemy(app)

# Datenbankmodell
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Eindeutige Datenbankeintrag-ID
    sensorid = db.Column(db.String(50), nullable=False)  # Sensor-ID
    sensortyp = db.Column(db.String(50), nullable=False)  # Typ des Sensors
    date = db.Column(db.Date, nullable=False)  # Datum der Messung
    time = db.Column(db.Time, nullable=False)  # Uhrzeit der Messung
    messungid = db.Column(db.String(50), nullable=False)  # Messung-ID
    wert = db.Column(db.Float, nullable=False)  # Wert der Messung
    einheit = db.Column(db.String(20), nullable=False)  # Einheit des Messwerts (z. B. °C)

# API-Route für das Empfangen von Sensordaten
@app.route('/sensor', methods=['POST'])
def receive_data():
    data = request.get_json()

    try:
        eintrag = SensorData(
            sensorid=data['sensorid'],
            sensortyp=data['sensortyp'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),  # Datum im richtigen Format umwandeln
            time=datetime.strptime(data['time'], '%H:%M:%S').time(),  # Zeit im richtigen Format umwandeln
            messungid=data['messungid'],
            wert=float(data['wert']),  # Wert als Gleitkommazahl
            einheit=data['einheit']
        )
        db.session.add(eintrag)
        db.session.commit()
        return jsonify({"status": "success", "id": eintrag.id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# App starten
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstelle die Tabellen in der SQLite-Datenbank, falls sie noch nicht existieren
    app.run(host='0.0.0.0', port=5000)  # Starte den Flask-Server
