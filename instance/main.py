from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True)
    arduino_id = Column(String(50), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    measurement_id = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    class_room = Column(String(50), nullable=False)

engine = create_engine("sqlite:///sensor_data.db")
Session = sessionmaker(bind=engine)
session = Session()

# Schritt 1: Raum für "undefined" anpassen
eintraege = session.query(SensorData).filter(SensorData.class_room == "undefined").yield_per(100)
for eintrag in eintraege:
    if eintrag.arduino_id and eintrag.arduino_id.lower() == "clara":
        eintrag.class_room = "2.16"
    elif eintrag.arduino_id and eintrag.arduino_id.lower() == "alina":
        eintrag.class_room = "1.42"

session.commit()

# Schritt 2: Prüfen, ob Alina-Daten mit Wert != 0 existieren
alina_daten = session.query(SensorData).filter(
    SensorData.arduino_id.ilike("alina"),
    SensorData.value != 0
).limit(1).all()

if alina_daten:
    # Schritt 3: Lösche Alina-Daten mit Wert 0 außer bei sensor_type == "Lautstärke"
    zu_loeschen = session.query(SensorData).filter(
        SensorData.arduino_id.ilike("alina"),
        SensorData.value == 0,
        SensorData.sensor_type != "Lautstärke"
    ).yield_per(100)

    count = 0
    for eintrag in zu_loeschen:
        session.delete(eintrag)
        count += 1

    session.commit()
    print(f"{count} Alina-Einträge mit Wert 0 (außer Lautstärke) gelöscht.")
else:
    print("Keine Alina-Daten mit Wert != 0 gefunden, keine Löschungen durchgeführt.")
