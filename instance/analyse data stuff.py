import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.orm import sessionmaker, declarative_base
import statistics # for average
import pexpect.popen_spawn as popen_spawn

Base = declarative_base()

# setup table stuff for database
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

# connect base and table to db
engine = create_engine("sqlite:///sensor_data_4.db")
Session = sessionmaker(bind=engine)
session = Session()

# GUI Mainwindow
root = tk.Tk()
root.title("Messdaten-Auswertung")

# dicts for saving bools for the options
sensor_vars = {}
class_vars = {}
arduino_vars = {}

status_label = ttk.Label(root, text="", foreground="blue")
status_label.grid(row=0, column=0, columnspan=3, pady=5)

# get data from db
def lade_werte():
    sensor_types = [r[0] for r in session.query(SensorData.sensor_type).distinct()]
    class_rooms = [r[0] for r in session.query(SensorData.class_room).distinct()]
    arduinos = [r[0] for r in session.query(SensorData.arduino_id).distinct()]

    # searches for distinct values in the db
    # for every new one creates new checkbox optioin

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

def daten_laden_status():
    status_label.config(text="Bitte warten, Daten werden geladen...")
    root.update_idletasks()

# looks at ticked boxes and
def daten_filtern():
    selected_sensors = [k for k, v in sensor_vars.items() if v.get()]
    selected_rooms = [k for k, v in class_vars.items() if v.get()]
    selected_arduinos = [k for k, v in arduino_vars.items() if v.get()]

    query = session.query(SensorData)
    if selected_sensors:
        query = query.filter(SensorData.sensor_type.in_(selected_sensors))
    if selected_rooms:
        query = query.filter(SensorData.class_room.in_(selected_rooms))
    if selected_arduinos:
        query = query.filter(SensorData.arduino_id.in_(selected_arduinos))

    daten = query.order_by(SensorData.date, SensorData.time).all()
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

    plt.figure("Auswertung", figsize=(12, 6))
    for key, data in gruppen.items():
        label = f"{key[0]} - Raum {key[1]} - {key[2]}"
        plt.plot(data["zeiten"], data["werte"], marker="o", label=label)

    plt.xticks(rotation=45)
    plt.xlabel("Zeit")
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

def datenbank_aktualisieren():
    zielpfad = filedialog.asksaveasfilename(
        title="Zielpfad für Datenbank auswählen",
        defaultextension=".db",
        filetypes=[("SQLite Datenbank", "*.db")],
        initialfile="sensor_data.db"
    )
    if not zielpfad:
        return

    status_label.config(text="Datenbank wird aktualisiert...")
    root.update_idletasks()

    remote_path = r"/Desktop/InfoPoject2025/instance/sensor_data_4.db"
    user_host = "info@10.29.0.170"
    scp_befehl = f"scp {user_host}:{remote_path} \"{zielpfad}\""

    try:
        child = popen_spawn.PopenSpawn(scp_befehl, timeout=30)
        child.expect("password:")
        child.sendline("info2025")
        child.expect(popen_spawn.EOF)
        status_label.config(text="Datenbank erfolgreich aktualisiert.")
    except Exception as e:
        status_label.config(text="Fehler bei der Datenbank-Aktualisierung.")
        messagebox.showerror("Fehler", f"Download fehlgeschlagen:\n{e}")

sensor_frame = ttk.LabelFrame(root, text="Sensor-Typ")
sensor_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

class_frame = ttk.LabelFrame(root, text="Klassenraum")
class_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nw")

arduino_frame = ttk.LabelFrame(root, text="Arduino ID")
arduino_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nw")

ttk.Button(root, text="Grafik generieren", command=grafik_generieren).grid(row=2, column=0, pady=10)
ttk.Button(root, text="Max/Min/Ø anzeigen", command=statistiken_anzeigen).grid(row=2, column=1, pady=10)
ttk.Button(root, text="Daten anzeigen", command=daten_anzeigen).grid(row=2, column=2, pady=10)

style = ttk.Style()
style.theme_use('clam')
style.configure("custom.Horizontal.TProgressbar", troughcolor='white', bordercolor='gray', background='#4CAF50', lightcolor='#4CAF50', darkcolor='#388E3C')

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", style="custom.Horizontal.TProgressbar")
progress.grid(row=3, column=0, columnspan=3, pady=5)

ttk.Button(root, text="Aktualisiere Datenbank", command=datenbank_aktualisieren).grid(row=4, column=0, columnspan=3, pady=10)

lade_werte()
root.mainloop()
