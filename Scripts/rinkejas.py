import obd
import time
import csv
import datetime
import os

# --- KONFIGŪRACIJA ---
PORT = "COM5"
file_name = "mokymo_duomenys.csv"


commands = [
    obd.commands.RPM,
    obd.commands.ENGINE_LOAD,
    obd.commands.COOLANT_TEMP,
    obd.commands.INTAKE_PRESSURE,
    obd.commands.SPEED,
    obd.commands.INTAKE_TEMP,
    obd.commands.MAF,
    obd.commands.FUEL_RAIL_PRESSURE_DIRECT,
    obd.commands.CONTROL_MODULE_VOLTAGE
]

def main():
    print("--- AUTOMATINIS DUOMENŲ RINKĖJAS ---")
    print(f"Failas: {file_name}")
    print("Norėdama(s) sustabdyti, paspausk CTRL + C")

    file_exists = os.path.isfile(file_name)

    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            header = ["Timestamp"] + [cmd.name for cmd in commands]
            writer.writerow(header)
            file.flush()

        while True:
            connection = None
            try:
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Bandoma jungtis prie {PORT}...")

                connection = obd.OBD(PORT, baudrate=9600, fast=False, timeout=5)

                if not connection.is_connected():
                    print("  -> Nepavyko. Bandysime vėl už 3 sek...")
                    time.sleep(3)
                    continue 
                
                print("  -> PRISIJUNGTA! Renkami duomenys...")

                row_count = 0
                while connection.is_connected():
                    row_data = [datetime.datetime.now().strftime("%H:%M:%S")]
                    valid_read = True
                    
                    for cmd in commands:
                        response = connection.query(cmd)
                        
                        if response.is_null():
                            valid_read = False
                            break
                        
                        val = response.value
                        
                        if hasattr(val, 'magnitude'):
                            val = val.magnitude
                        
                        row_data.append(val)
                        
                    if valid_read:
                        writer.writerow(row_data)
                        file.flush()
                        row_count += 1
                        
                        if row_count % 5 == 0:
                            print(f"\rĮrašyta eilučių: {row_count} | RPM: {row_data[1]} | Greitis: {row_data[5]}", end="")
                    
                    time.sleep(2.5) 

                print("\n  -> Ryšys nutrūko. Bandoma jungtis iš naujo...")

            except KeyboardInterrupt:
                print("\n\nStabdoma vartotojo prašymu.")
                if connection: connection.close()
                return

            except Exception as e:
                print(f"\n  -> Klaida: {e}")
                time.sleep(3)

if __name__ == "__main__":
    main()