import obd
import time
import datetime
import json
import ssl
import paho.mqtt.client as mqtt
import serial


HOST = 'eu.thingsboard.cloud'
TOKEN = 'wDqMhRLCdPpQxkmVoPGF'
MQTT_PORT = 1883
MQTT_TOPIC = "v1/devices/me/telemetry"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(TOKEN)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("[MQTT] Prisijungta prie ThingsBoard")
    else:
        print(f"[MQTT] Klaida jungiantis, kodas: {rc}")
        
client.on_connect = on_connect

try:
    client.connect(HOST, MQTT_PORT, 60)
    print("Prisijungta sekmingai")
    client.loop_start()
except Exception as e:
    print(f"Nepavyko prisijungti: {e}")


command_queue = [
    obd.commands.RPM,
    obd.commands.ENGINE_LOAD,
    obd.commands.COOLANT_TEMP,
    obd.commands.INTAKE_PRESSURE,
    obd.commands.SPEED,
    obd.commands.INTAKE_TEMP,
    obd.commands.MAF,
    obd.commands.FUEL_RAIL_PRESSURE_DIRECT,
    obd.commands.COMMANDED_EGR,
    obd.commands.EGR_ERROR,
    obd.commands.CONTROL_MODULE_VOLTAGE,
    obd.commands.GET_DTC
]


data_headers = [cmd.name for cmd in command_queue]

laikas = datetime.datetime.now().isoformat()

try:
    connection = obd.OBD("COM5", baudrate=9600, fast=False)
except Exception as e:
    print(f"Klaida jungiantis prie OBD: {e}")
    connection = None
    

try:
    while True:
        if connection is None or not connection.is_connected():
            print("Bandoma jungtis prie automobilio")
            try:
                connection = obd.OBD("COM5", baudrate=9600, fast=False, timeout=4)
                
                if not connection_is_connected():
                    print("Nepavyko prisijungti. Bus bandoma uz 3 sekundziu.")
                    connection = None
                    time.sleep(3)
                    continue
                else:
                    print("Sekmingai prisijungta prie automobilio")
            except Exception as e:
                print(f"Klaida jungiantis prie OBD: {e}")
                connection = None
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
                            # Sumažinome ribą iki 1.5 (jautriau)
                            if dev > 1.5 and dev > max_deviation:
                                max_deviation = dev
                                suspect_text = f"\n⚠️ Įtartina: {param} -> {int(curr_val)}"
                    
                    # --- 2. LOGINIAI SPĖJIMAI (Santykių analizė) ---
                    # Jei Z-Score nieko nerado, bandome atspėti pagal logiką
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
                

