import csv
import struct
import os
import sys

# === CONFIGURAZIONE ===
INPUT_FILENAME = 'sked-b25.csv'
OUTPUT_FILENAME = 'EIBI.DAT'
STATION_NAME_LEN = 20

# --- NUOVA MAPPATURA COLONNE ---
COL_FREQ = 0    
COL_TIME = 1    
COL_NAME = 4    

def time_to_minutes(hhmm_str):
    try:
        hhmm_str = hhmm_str.strip()
        hh = int(hhmm_str[0:2])
        mm = int(hhmm_str[2:4])
        return hh * 60 + mm
    except:
        return 0

def create_binary_db():
    # --- MAGIA PER TROVARE IL PERCORSO GIUSTO ---
    # Trova la cartella dove risiede fisicamente questo script .py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crea i percorsi completi unendo la cartella al nome del file
    full_input_path = os.path.join(script_dir, INPUT_FILENAME)
    full_output_path = os.path.join(script_dir, OUTPUT_FILENAME)

    print(f"\n--- ELABORAZIONE ---")
    print(f"Cerco il file qui: {full_input_path}")
    
    records = []
    
    try:
        # Usiamo full_input_path invece del nome breve
        with open(full_input_path, mode='r', encoding='latin-1', errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            
            for row in reader:
                if not row or len(row) <= COL_NAME:
                    continue
                
                try:
                    freq_raw = row[COL_FREQ]
                    if "kHz" in str(freq_raw): continue 
                    
                    freq_khz = int(float(freq_raw))
                    
                    if freq_khz <= 0 or freq_khz > 30000:
                        continue

                    time_raw = row[COL_TIME]
                    if '-' in time_raw:
                        parts = time_raw.split('-')
                        t_start = time_to_minutes(parts[0])
                        t_end = time_to_minutes(parts[1])
                    else:
                        t_start = 0
                        t_end = 1440 

                    station_name = row[COL_NAME]
                    clean_name = station_name.encode('ascii', 'ignore').decode('ascii')
                    
                    records.append({
                        'freq': freq_khz,
                        'start': t_start,
                        'end': t_end,
                        'name': clean_name
                    })
                    
                except ValueError:
                    continue

        print(f"Trovati {len(records)} record validi. Ordinamento...")
        records.sort(key=lambda x: x['freq'])

        print(f"Scrittura di {OUTPUT_FILENAME}...")
        # Usiamo full_output_path
        with open(full_output_path, 'wb') as binfile:
            for rec in records:
                name_bytes = rec['name'].ljust(STATION_NAME_LEN)[:STATION_NAME_LEN].encode('utf-8')
                binary_data = struct.pack('<HHH20s', 
                                          rec['freq'], 
                                          rec['start'], 
                                          rec['end'], 
                                          name_bytes)
                binfile.write(binary_data)

        print(f"--- COMPLETATO ---")
        print(f"File creato in: {full_output_path}")
        print(f"Dimensione: {os.path.getsize(full_output_path)} bytes")
        
        print("\nEsempio primi 3 record generati:")
        for i in range(min(3, len(records))):
            print(f"Freq: {records[i]['freq']} | Nome: {records[i]['name']}")

    except FileNotFoundError:
        print(f"\nERRORE CRITICO:\nIl file non è stato trovato in:\n{full_input_path}")
        print("\nAssicurati che 'sked-b25.csv' sia nella stessa cartella dello script.")

if __name__ == "__main__":
    create_binary_db()