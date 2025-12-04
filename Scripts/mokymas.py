import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

FAILAS = 'mokymo_duomenys.csv'
MODELIO_FAILAS = 'automobilio_modelis.pkl'

FEATURES = [
    'RPM', 'ENGINE_LOAD', 'COOLANT_TEMP', 'INTAKE_PRESSURE', 
    'SPEED', 'INTAKE_TEMP', 'MAF', 'FUEL_RAIL_PRESSURE_DIRECT', 
    'CONTROL_MODULE_VOLTAGE'
]

def train_and_test():
    print("Kraunami duomenys...")
    df = pd.read_csv(FAILAS)
    
    X = df[FEATURES]
    
    print("Mokomas DI modelis (Contamination=0.05)...")
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)
    
    joblib.dump(model, MODELIO_FAILAS)
    print(f"✅ Naujas modelis išsaugotas: {MODELIO_FAILAS}")
    
    print("\n--- TESTUOJAME MODELĮ ---")
    
    test_data = {
        'RPM': 5000, 
        'ENGINE_LOAD': 100, 
        'COOLANT_TEMP': 90, 
        'INTAKE_PRESSURE': 150, 
        'SPEED': 0,     
        'INTAKE_TEMP': 20, 
        'MAF': 50, 
        'FUEL_RAIL_PRESSURE_DIRECT': 40000, 
        'CONTROL_MODULE_VOLTAGE': 14.0
    }
    
    df_test = pd.DataFrame([test_data])
    prediction = model.predict(df_test)[0]
    
    if prediction == -1:
        print("REZULTATAS: ⚠️ ANOMALIJA (Testas pavyko!)")
        print("Modelis teisingai suprato, kad 5000 RPM stovint yra nenormalu.")
    else:
        print("REZULTATAS: ✅ NORMA (Testas nepavyko)")
        print("Modelis vis dar per daug atlaidus. Reikia didinti contamination.")

if __name__ == "__main__":
    train_and_test()