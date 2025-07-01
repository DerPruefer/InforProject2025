import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.orm import sessionmaker, declarative_base
import statistics
import pexpect

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

root = tk.Tk()
root.title("Messdaten-Auswertung")

sensor_vars = {}
class_vars = {}
arduino_vars = {}
tage_vars = {}

status_label = ttk.Label(root, text="", foreground="blue")
status_label.grid(row=0, column=0, columnspan=3, pady=5)

anzahl_label = ttk.Label(root, text="Datensätze: 0", foreground="green")
anzahl_label.grid(row=0, column=5, sticky="w", padx=5)

def lade_werte():
    sensor_types = [r[0] for r in session.query(SensorData.sensor_type).distinct()]
    class_rooms = [r[0] for r in session.query(SensorData.class_room).distinct()]
    arduinos = [r[0] for r in session.query(SensorData.arduino_id).distinct()]
    daten_tage = [str(r[0]) for r in session.query(SensorData.date).distinct().order_by(SensorData.date)]

    for i, sensor in enumerate(sensor_types):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(sensor_frame, text=sensor, variable=var)
        cb.grid(row=i, column=0, sticky="w")
        sensor_vars[sensor] = var

    for i, room in enumerate(class_rooms):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(class_frame, text=room, variable=var)
        cb.grid(row=i, column=0, sticky="w")
        class_vars[room] = var

    for i, arduino in enumerate(arduinos):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(arduino_frame, text=arduino, variable=var)
        cb.grid(row=i, column=0, sticky="w")
        arduino_vars[arduino] = var

    for i, tag in enumerate(daten_tage):
        var = tk.BooleanVar()
        cb = tk.Checkbutton(tage_frame, text=tag, variable=var)
        cb.grid(row=i, column=0, sticky="w")
        tage_vars[tag] = var

def daten_laden_status():
    status_label.config(text="Bitte warten, Daten werden geladen...")
    root.update_idletasks()

def daten_filtern():
    selected_sensors = [k for k, v in sensor_vars.items() if v.get()]
    selected_rooms = [k for k, v in class_vars.items() if v.get()]
    selected_arduinos = [k for k, v in arduino_vars.items() if v.get()]
    selected_tage = [k for k, v in tage_vars.items() if v.get()]

    query = session.query(SensorData)
    if selected_sensors:
        query = query.filter(SensorData.sensor_type.in_(selected_sensors))
    if selected_rooms:
        query = query.filter(SensorData.class_room.in_(selected_rooms))
    if selected_arduinos:
        query = query.filter(SensorData.arduino_id.in_(selected_arduinos))
    if selected_tage:
        from datetime import datetime
        tage = [datetime.strptime(tag, "%Y-%m-%d").date() for tag in selected_tage]
        query = query.filter(SensorData.date.in_(tage))

    daten = query.order_by(SensorData.date, SensorData.time).all()
    anzahl_label.config(text=f"Datensätze: {len(daten)}")
    return daten

def grafik_generieren():
    daten_laden_status()
    daten = daten_filtern()
    if not daten:
        status_label.config(text="")
        progress["value"] = 0
        root.update_idletasks()
        messagebox.showinfo("Keine Daten", "Keine Messdaten gefunden.")
        return

    gruppen = {}
    total = len(daten)
    for idx, d in enumerate(daten, 1):
        key = (d.sensor_type, d.class_room, d.arduino_id)
        gruppen.setdefault(key, {"zeiten": [], "werte": [], "unit": d.unit})
        gruppen[key]["zeiten"].append(f"{d.date} {d.time}")
        gruppen[key]["werte"].append(d.value)

        progress["value"] = (idx / total) * 100
        root.update_idletasks()

    status_label.config(text="")
    progress["value"] = 100
    root.update_idletasks()

    import matplotlib.dates as mdates
    from datetime import datetime

    plt.figure("Auswertung", figsize=(12, 6))
    for key, data in gruppen.items():
        zeiten = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f") for t in data["zeiten"]]
        plt.plot(zeiten, data["werte"], marker="o", label=f"{key[0]} - Raum {key[1]} - {key[2]}")

    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
    plt.gcf().autofmt_xdate()

    plt.xlabel("Zeit")
    if len(gruppen) == 1:
        eintrag = list(gruppen.values())[0]
        plt.ylabel(f"Wert in {eintrag['unit']}")
        plt.title(f"Messreihe: {list(gruppen.keys())[0][0]}")
    else:
        plt.ylabel("Wert")
        plt.title("Messdaten-Auswertung")

    plt.legend()
    plt.tight_layout()
    plt.show()

    progress["value"] = 0
    root.update_idletasks()

def statistiken_anzeigen():
    daten_laden_status()
    daten = daten_filtern()
    if not daten:
        status_label.config(text="")
        messagebox.showinfo("Keine Daten", "Keine Messdaten gefunden.")
        return

    gruppen = {}
    for d in daten:
        key = (d.sensor_type, d.class_room, d.arduino_id)
        gruppen.setdefault(key, []).append(d)

    ausgabe = ""
    for key, daten_liste in gruppen.items():
        werte = [d.value for d in daten_liste]
        minimum = min(werte)
        maximum = max(werte)
        durchschnitt = round(statistics.mean(werte), 2)

        min_daten = [d for d in daten_liste if d.value == minimum][0]
        max_daten = [d for d in daten_liste if d.value == maximum][0]

        ausgabe += f"{key[0]} - Raum {key[1]} - Arduino {key[2]}:\n"
        ausgabe += f"  ➔ Min: {minimum} {min_daten.unit} am {min_daten.date} um {min_daten.time}\n"
        ausgabe += f"  ➔ Max: {maximum} {max_daten.unit} am {max_daten.date} um {max_daten.time}\n"
        ausgabe += f"  ➔ Ø: {durchschnitt}\n\n"

    status_label.config(text="")
    messagebox.showinfo("Statistiken", ausgabe)

def daten_anzeigen():
    daten_laden_status()
    daten = daten_filtern()
    if not daten:
        status_label.config(text="")
        messagebox.showinfo("Keine Daten", "Keine Messdaten gefunden.")
        return

    text = "\n".join(
        f"{d.date} {d.time} | {d.sensor_type} | Raum {d.class_room} | {d.value} {d.unit} | Arduino {d.arduino_id}"
        for d in daten
    )

    status_label.config(text="")
    fenster = tk.Toplevel(root)
    fenster.title("Messdaten")
    textfeld = tk.Text(fenster, width=120, height=40)
    textfeld.insert("1.0", text)
    textfeld.pack()

def sql_ausfuehren():
    fenster = tk.Toplevel(root)
    fenster.title("Manuelle SQL-Abfrage")
    fenster.geometry("800x600")

    label = ttk.Label(fenster, text="SQL-Befehl:")
    label.pack()

    eingabe = tk.Text(fenster, height=5)
    eingabe.pack(fill=tk.X)

    ausgabe = tk.Text(fenster, height=25)
    ausgabe.pack(fill=tk.BOTH, expand=True)

    from sqlalchemy import text

    def ausfuehren():
        try:
            befehl = eingabe.get("1.0", "end").strip()
            ausgabe.delete("1.0", "end")

            if befehl.lower().startswith("select"):
                with engine.connect() as connection:
                    result = connection.execute(text(befehl))
                    for zeile in result:
                        ausgabe.insert("end", f"{zeile}\n")
            else:
                with engine.begin() as connection:
                    connection.execute(text(befehl))
                    ausgabe.insert("end", "Befehl erfolgreich ausgeführt.")
        except Exception as e:
            ausgabe.insert("end", f"Fehler: {e}")

    ttk.Button(fenster, text="Ausführen", command=ausfuehren).pack()

sensor_frame = ttk.LabelFrame(root, text="Sensor-Typ")
sensor_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

class_frame = ttk.LabelFrame(root, text="Klassenraum")
class_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nw")

arduino_frame = ttk.LabelFrame(root, text="Arduino ID")
arduino_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nw")

tage_frame = ttk.LabelFrame(root, text="Tage")
tage_frame.grid(row=1, column=3, rowspan=2, padx=10, pady=10, sticky="nw")

ttk.Button(root, text="Grafik generieren", command=grafik_generieren).grid(row=2, column=0, pady=10)
ttk.Button(root, text="Max/Min/Ø anzeigen", command=statistiken_anzeigen).grid(row=2, column=1, pady=10)
ttk.Button(root, text="Daten anzeigen", command=daten_anzeigen).grid(row=2, column=2, pady=10)

style = ttk.Style()
style.theme_use('clam')
style.configure("custom.Horizontal.TProgressbar", troughcolor='white', bordercolor='gray', background='#4CAF50', lightcolor='#4CAF50', darkcolor='#388E3C')

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", style="custom.Horizontal.TProgressbar")
progress.grid(row=3, column=0, columnspan=3, pady=5)

ttk.Button(root, text="SQL ausführen", command=sql_ausfuehren).grid(row=4, column=0, columnspan=3, pady=10)

lade_werte()
root.mainloop()
