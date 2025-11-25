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
            print("Nera rysio su automobiliu")
            try:
                connection = obd.OBD("COM5", baudrate=9600, fast=False)
            except:
                time.sleep(2)
                continue
        
        info_dict = {}
        
        print(f"[{time.strftime('%H:%M:%S')}] Nuskaitomi duomenys")
        
        for cmd in command_queue:
            try:
                response = connection.query(cmd)
                
                if response.value is not None:
                    if hasattr(response.value, 'magnitude'):
                        info_dict[cmd.name] = response.value.magnitude
                    else:
                        info_dict[cmd.name] = response.value
                else:
                    pass
            except Exception as e:
                print(f"Klaida nuskaitant {cmd.name}: {e}")
                
        
        if info_dict:
            try:
                telemetry_payload = json.dumps(info_dict)
                
                client.publish(MQTT_TOPIC, telemetry_payload, qos=1)
                
                print(f"Duomenys issiusti: {info_dict}")
            except Exception as e:
                print(f"Klaida siunciant duomenis: {e}")
                
except KeyboardInterrupt:
    print("Programa nutraukiama")
    if connection:
        connection.close()
    client.loop_stop()
    client.disconnect()
    print("Programa isjungta")
                

