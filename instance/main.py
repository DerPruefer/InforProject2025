import requests

# ➤ URL deines Flask-Servers
url = "http://10.29.0.170:5000/sensor"  # ggf. IP/Port anpassen

# ➤ Testdaten: Temperatur = 0
test_daten = [
    {
        "arduino_id": "Alina",
        "sensor_type": "Temperatur",
        "measurement_id": "T-001",
        "value": 0,
        "unit": "°C",
        "class_room": "R1"
    }
]

# ➤ POST-Anfrage senden
response = requests.post(url, json=test_daten)

# ➤ Ausgabe
print("Status Code:", response.status_code)
print("Antwort:", response.json())
