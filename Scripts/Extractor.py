import obd
import time
import serial.serialutil
import sqlite3
import sys


def sukurti_duomenu_baze(db_name, header_list):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        
        column_definitions = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "timestamp DATETIME NOT NULL"
        ]
        
        for cmd_name in header_list:
            if cmd_name == "GET_DTC":
                column_definitions.append(f"'{cmd_name}' TEXT")
            else:
                column_definitions.append(f"'{cmd_name}' REAL")
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS readings (
            {', '.join(column_definitions)}
        );
        """
        
        c.execute(create_table_sql)
        
        # 5 žingsnis: Išsaugojimas
        conn.commit()
        conn.close()
        print("Duomenų bazės lentelė sėkmingai paruošta.")
    
    except sqlite3.Error as e:
        # 5 žingsnis: Klaidų gaudymas
        print(f"KLAIDA: Nepavyko sukurti SQLite lentelės: {e}")
        print("Programa bus sustabdyta.")
        sys.exit() # Svarbu sustoti, jei DB paruošimas nepavyko

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

db_file_name = r"C:\Users\giedr\Desktop\BD\dash\workspace\shadcn-ui\public\auto_data1.db"

data_headers = [cmd.name for cmd in command_queue]

sukurti_duomenu_baze(db_file_name, data_headers)

try:
    while True:
        info_dict = {}
        connection = None
        connection_successfull = False
        try:
        
            connection = obd.OBD("COM5", baudrate=9600)
        
            if(connection.is_connected()):
                print(f"[{time.strftime('%H:%M:%S')}] Prisijungta, skaitomi duomenys...")
                connection_successfull = True
                for cmd in command_queue:
                    response = connection.query(cmd)
                
                    if response.value is not None:
                        if cmd.name == "GET_DTC":
                            print("GET_DTC")
                        else:
                            info_dict[cmd.name] = response.value.magnitude
                    elif response.value is None:
                        info_dict[cmd.name] = None
        
        except (serial.serialutil.SerialError, PermissionError) as e:
            print(f"[{time.strftime('%H:%M:%S')}] COM Prievado klaida: {e}")
            print("Patikrinkite, ar kita programa nenaudoja COM5.")
        
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Įvyko netikėta klaida: {e}")
        
        finally:
            if connection is not None and connection.is_connected():
                connection.close()
                print(f"[{time.strftime('%H:%M:%S')}] Ryšys uždarytas.")
        
        if connection_successfull is True:
            try:
                row_data = [time.strftime("%Y-%m-%d %H:%M:%S")]
            
                for cmd_name in data_headers:
                    row_data.append(info_dict.get(cmd_name))
            
                column_names = ['timestamp'] + data_headers
                placeholders = ', '.join(['?'] * len(column_names))
                
                sql_query = f"INSERT INTO readings ({', '.join(column_names)}) VALUES ({placeholders})"
                
                conn = sqlite3.connect(db_file_name)
                c = conn.cursor()
                c.execute(sql_query, row_data)
                conn.commit()
                conn.close()
                
                print(f"[{time.strftime('%H:%M:%S')}] Duomenys sėkmingai įrašyti į SQLite DB.")
                
            except sqlite3.Error as e:
                print(f"[{time.strftime('%H:%M:%S')}] KLAIDA: Nepavyko įrašyti į SQLite: {e}")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] KLAIDA: Netikėta DB rašymo klaida: {e}")
                
        else:
             print(f"[{time.strftime('%H:%M:%S')}] Nėra ryšio su automobiliu (praleidžiamas DB įrašymas).")
             
        time.sleep(0.8)
    
except(KeyboardInterrupt):
    exit()

