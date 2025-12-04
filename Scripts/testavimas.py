import pandas as pd
import joblib

print("Kraunamas modelis...")
model = joblib.load('automobilio_modelis.pkl')

FEATURES = [
    'RPM', 'ENGINE_LOAD', 'COOLANT_TEMP', 'INTAKE_PRESSURE', 
    'SPEED', 'INTAKE_TEMP', 'MAF', 'FUEL_RAIL_PRESSURE_DIRECT', 
    'CONTROL_MODULE_VOLTAGE'
]

def tikrinti(pavadinimas, duomenys):
    df = pd.DataFrame([duomenys], columns=FEATURES)
    
    rezultatas = model.predict(df)[0]
    
    statusas = "✅ NORMA" if rezultatas == 1 else "❌ ANOMALIJA"
    print(f"Scenarijus: {pavadinimas}")
    print(f"  -> {statusas}")
    print("-" * 30)

# --- TESTAVIMO SCENARIJAI ---

# 1. Normalus važiavimas 
tikrinti("Ramus važiavimas", {
    'RPM': 2000, 'ENGINE_LOAD': 30, 'COOLANT_TEMP': 85, 'INTAKE_PRESSURE': 30, 
    'SPEED': 50, 'INTAKE_TEMP': 20, 'MAF': 10, 'FUEL_RAIL_PRESSURE_DIRECT': 30000, 
    'CONTROL_MODULE_VOLTAGE': 14.0
})

# 2. Variklio perkaitimas 
tikrinti("Perkaitimas kamštyje", {
    'RPM': 800, 'ENGINE_LOAD': 15, 'COOLANT_TEMP': 200, 'INTAKE_PRESSURE': 30, 
    'SPEED': 0, 'INTAKE_TEMP': 40, 'MAF': 5, 'FUEL_RAIL_PRESSURE_DIRECT': 28000, 
    'CONTROL_MODULE_VOLTAGE': 13.5
})

# 3. Milziniskos apsukos stovint vietoje
tikrinti("Gazavimas vietoje", {
    'RPM': 6000, 'ENGINE_LOAD': 80, 'COOLANT_TEMP': 90, 'INTAKE_PRESSURE': 90, 
    'SPEED': 0, 'INTAKE_TEMP': 25, 'MAF': 50, 'FUEL_RAIL_PRESSURE_DIRECT': 40000, 
    'CONTROL_MODULE_VOLTAGE': 14.2
})

# 4. Sugedęs generatorius
tikrinti("Generatoriaus gedimas", {
    'RPM': 2500, 'ENGINE_LOAD': 40, 'COOLANT_TEMP': 88, 'INTAKE_PRESSURE': 40, 
    'SPEED': 90, 'INTAKE_TEMP': 20, 'MAF': 20, 'FUEL_RAIL_PRESSURE_DIRECT': 32000, 
    'CONTROL_MODULE_VOLTAGE': 11.0
})