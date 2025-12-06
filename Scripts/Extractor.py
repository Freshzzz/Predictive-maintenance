import obd
import time
import datetime
import json
import ssl
import paho.mqtt.client as mqtt
import serial
import socket
import requests
import joblib
import pandas as pd


# MQTT / ThingsBoard nustatymai
TB_HOST = 'eu.thingsboard.cloud'
TB_PORT = 1883
MQTT_TOPIC = "v1/devices/me/telemetry"

# OBD Nustatymai
# OBD_PORT = "/dev/rfcomm0"
OBD_PORT = "COM5"

# Telegram Nustatymai
T_CHAT_ID = "5761356600"


# Automobilio kritines ribos
MAX_TEMP = 105 # Maksimali aušinimo skysčio temperatūra °C
MIN_VOLTAGE = 11.5  # Minimali akumuliatoriaus įtampa V
MAX_VOLTAGE = 15.2  # Maksimali akumuliatoriaus įtampa V
MAX_RPM = 4000  # Maksimalios apsukos RPM
MAX_MAF = 255  # Maksimalus oro srautas g/s
MAX_FUEL_PRESSURE = 180000  # Maksimalus kuro slėgis kPa
ALERT_COOLDOWN = 60
last_alert_time = 0


# DI Nustatymai
MODEL_FILE = "automobilio_modelis.pkl"
MODEL_FEATURES = ['RPM', 'ENGINE_LOAD', 'COOLANT_TEMP', 'INTAKE_PRESSURE', 'SPEED', 'INTAKE_TEMP', 'MAF', 'FUEL_RAIL_PRESSURE_DIRECT', 'CONTROL_MODULE_VOLTAGE']
model = None

HISTORY_SIZE = 10
ANOMALY_THRESHOLD = 0.6
ai_history = [0] * HISTORY_SIZE

print("Prijungiamas DI Modelis...")
try:
    model = joblib.load(MODEL_FILE)
    print("DI Modelis sekmingai prijungtas")
except Exception as e:
    print(f"Klaida prijungiant DI modelį: {e}")
    model = None


# OBD komandų sąrašas
command_queue = [
    obd.commands.RPM,
    obd.commands.ENGINE_LOAD,
    obd.commands.COOLANT_TEMP,
    obd.commands.INTAKE_PRESSURE,
    obd.commands.SPEED,
    obd.commands.INTAKE_TEMP,
    obd.commands.MAF,
    obd.commands.FUEL_RAIL_PRESSURE_DIRECT,
    obd.commands.CONTROL_MODULE_VOLTAGE,
    obd.commands.GET_DTC
]

# Mokymo duomenų statistika (vidurkiai ir standartiniai nuokrypiai)
TRAIN_STATS = {
    'RPM': (1584, 649),
    'SPEED': (58, 40),
    'ENGINE_LOAD': (40, 25),
    'COOLANT_TEMP': (73, 20),
    'INTAKE_PRESSURE': (104, 24),
    'MAF': (26, 14),
    'FUEL_RAIL_PRESSURE_DIRECT': (60308, 34337),
    'CONTROL_MODULE_VOLTAGE': (13.9, 0.4)
}

def check_limits(data):
    temp = data.get('COOLANT_TEMP')
    if temp is not None and temp > 105:
        return True, f"Perkaites ausinimo skystis: {temp}°C"
    
    rpm = data.get('RPM')
    if rpm is not None and rpm > MAX_RPM:
        return True, f"Perdaug apsuku variklyje: {rpm} RPM"
    
    voltage = data.get('CONTROL_MODULE_VOLTAGE')
    if voltage is not None and voltage < MIN_VOLTAGE:
        return True, f"Per maza akumuliatoriaus itampa: {voltage} V"
    if voltage is not None and voltage > MAX_VOLTAGE:
        return True, f"Per didele akumuliatoriaus itampa: {voltage} V"
    
    maf = data.get('MAF')
    if maf is not None and maf > MAX_MAF:
        return True, f"Per didelis oro srautas i varikli: {maf} g/s"
    
    fuel_pressure = data.get('FUEL_RAIL_PRESSURE_DIRECT')
    if fuel_pressure is not None and fuel_pressure > MAX_FUEL_PRESSURE:
        return True, f"Per didelis kuro slėgis: {int(fuel_pressure/100)} Bar"
    
    return False, None

def wait_for_internet():
    print("Laukiama interneto ryšio")
    while True:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            print("Internetas atsirado")
            return
        except OSError:
            time.sleep(2)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] Prisijungta prie ThingsBoard")
    else:
        print(f"[MQTT] Klaida jungiantis, kodas: {rc}")


def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{T_TOKEN}/sendMessage"
        payload = {
            "chat_id": T_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
            }
        requests.post(url, json=payload, timeout=2)
        print(f"Zinute i telegram issiusta")
    except Exception as e:
        print(f"Nepavyko issiusti zinutes i telegram: {e}")
        
        
def get_obd_connection():
    print(f"Bandoma prisijungti prie automobilio")
    try:
        conn = obd.OBD(OBD_PORT, baudrate=9600, fast=False, timeout=4)
        if conn.is_connected():
            print("Sekmingai prisijungta prie automobilio")
            return conn
        else:
            print("Prisijungti prie automobilio nepavyko")
            return None
    except Exception as e:
        print(f"Klaida bandant prisijungti prie automobilio: {e}")
        return None
        

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(TB_TOKEN)    
client.on_connect = on_connect

wait_for_internet()

try:
    client.connect(TB_HOST, TB_PORT, 60)
    print("Prisijungta sekmingai")
    client.loop_start()
except Exception as e:
    print(f"Nepavyko prisijungti prie serverio: {e}")

connection = None

try:
    while True:
        if connection is None or not connection.is_connected():
            connection = get_obd_connection()
            if connection is None:
                time.sleep(3)
                continue
        
        info_dict = {}
        
        print(f"[{time.strftime('%H:%M:%S')}] Nuskaitomi duomenys")
        
        try:
            if connection.status() == obd.OBDStatus.NOT_CONNECTED:
                raise Exception("Nutruko rysys")
            
            for cmd in command_queue:
                response = connection.query(cmd)
                
                if response is None:
                    continue
                
                if response.value is not None:
                    if hasattr(response.value, 'magnitude'):
                        info_dict[cmd.name] = response.value.magnitude
                    else:
                        info_dict[cmd.name] = response.value
                
        except Exception as e:
            print(f"Klaida nuskaitant duomenis: {e}")
            print("Perkraunamas rysys")
            try:
                connection.close()
            except:
                pass
            connection = None
            time.sleep(2)
            continue
                
        
        if info_dict:
            critical_anomaly, critical_message = check_limits(info_dict)

            current_ai_result = 0

            if model is not None:
                try:
                    input_data = {}

                    for feature in MODEL_FEATURES:
                        input_data[feature] = info_dict.get(feature, 0)
                    
                    df_predict = pd.DataFrame([input_data])
                    prediction = model.predict(df_predict)[0]

                    if prediction == -1:
                        current_ai_result = 1

                except Exception as e:
                    print(f"Klaida naudojant DI modeli: {e}")

            ai_history.append(current_ai_result)
            if len(ai_history) > HISTORY_SIZE:
                ai_history.pop(0)

            ai_score = sum(ai_history) / len(ai_history)
            ai_final_anomaly = 1 if ai_score >= ANOMALY_THRESHOLD else 0
            is_final_anomaly = critical_anomaly or ai_final_anomaly

            if is_final_anomaly:
                info_dict['Anomaly'] = 1

                if critical_anomaly:
                    info_dict['Anomaly_Type'] = "Critical"
                    alert_msg = critical_message
                else:
                    info_dict['Anomaly_Type'] = "AI"
                    
                    suspect_text = ""
                    max_deviation = 0
                    
                    for param, (mean, std) in TRAIN_STATS.items():
                        curr_val = info_dict.get(param, 0)
                        if std > 0:
                            dev = abs(curr_val - mean) / std
                            if dev > 1.5 and dev > max_deviation:
                                max_deviation = dev
                                suspect_text = f"\n⚠️ Įtartina: {param} -> {int(curr_val)}"
                    
                    if suspect_text == "":
                        rpm = info_dict.get('RPM', 0)
                        speed = info_dict.get('SPEED', 0)
                        load = info_dict.get('ENGINE_LOAD', 0)
                        
                        if rpm > 2500 and speed < 5:
                            suspect_text = "\n⚠️ Aukštos apsukos stovint"
                        elif load > 80 and speed < 5:
                            suspect_text = "\n⚠️ Didelė apkrova stovint"
                        elif rpm < 800 and speed > 60:
                            suspect_text = "\n⚠️ Riedėjimas laisva pavara?"
                        else:
                            suspect_text = "\n(Neįprasta parametrų kombinacija)"

                    alert_msg = f"🤖 DI aptiko anomaliją ({int(ai_score*100)}% tikimybė){suspect_text}"

                current_time = time.time()
                if current_time - last_alert_time > ALERT_COOLDOWN:
                    full_alert_msg = (f"⚠️ DEMESIO ⚠️ \n\n"
                                      f"{alert_msg} \n"
                                      f"Laikas: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    send_telegram_alert(full_alert_msg)
                    last_alert_time = current_time
            else:
                info_dict['Anomaly'] = 0
                info_dict['Anomaly_Type'] = "None"

            try:
                telemetry_payload = json.dumps(info_dict)
                client.publish(MQTT_TOPIC, telemetry_payload, qos=1)
                print(f"Duomenys issiusti i TB: {info_dict['Anomaly']} | DI Istorija: {ai_history} | DI Balas: {int(ai_score*100)}%")
            except Exception as e:
                print(f"Klaida siunciant duomenis i TB: {e}")
                    
            
        
        time.sleep(2)
                
except KeyboardInterrupt:
    print("Programa nutraukiama")
    if connection:
        connection.close()
    client.loop_stop()
    client.disconnect()
    print("Programa isjungta")
                

