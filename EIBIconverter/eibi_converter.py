import csv
import struct
import os

# === CONFIGURAZIONE ===
INPUT_FILENAME = 'sked-b25.csv'
OUTPUT_FILENAME = 'EIBI.DAT'
STATION_NAME_LEN = 20

# Mappatura Colonne (EIBI Standard: A=0, B=1, etc.)
COL_FREQ = 0    # kHz
COL_TIME = 1    # Time
COL_NAME = 4    # Station (Colonna E)

def time_to_minutes(hhmm_str):
    try:
        hhmm_str = hhmm_str.strip()
        if not hhmm_str: return 0
        hh = int(hhmm_str[0:2])
        mm = int(hhmm_str[2:4])
        return hh * 60 + mm
    except:
        return 0

def create_binary_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_input_path = os.path.join(script_dir, INPUT_FILENAME)
    full_output_path = os.path.join(script_dir, OUTPUT_FILENAME)

    print(f"\n--- CONVERTITORE EIBI GOLDENRADIO ---")
    
    records = []
    
    try:
        with open(full_input_path, mode='r', encoding='latin-1', errors='replace') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            
            for row in reader:
                # Salta righe vuote o troppo corte
                if not row or len(row) <= COL_NAME: continue
                
                try:
                    # 1. Frequenza
                    freq_raw = row[COL_FREQ]
                    if "kHz" in str(freq_raw): continue # Salta l'intestazione
                    
                    freq_khz = int(float(freq_raw))
                    
                    # FILTRO: Ignoriamo VLF (< 100 kHz) e frequenze assurde (> 30 MHz)
                    # Questo rimuove i sottomarini e tiene solo le radio ascoltabili
                    if freq_khz < 10 or freq_khz > 30000: continue

                    # 2. Orario
                    time_raw = row[COL_TIME]
                    if '-' in time_raw:
                        parts = time_raw.split('-')
                        t_start = time_to_minutes(parts[0])
                        t_end = time_to_minutes(parts[1])
                    else:
                        t_start = 0
                        t_end = 1440 

                    # 3. Nome Stazione (Colonna 4!)
                    station_name = row[COL_NAME]
                    
                    # Pulizia nome: convertiamo in ASCII puro per evitare caratteri strani sul display
                    clean_name = station_name.encode('ascii', 'ignore').decode('ascii').strip()
                    
                    if not clean_name: clean_name = "Unknown"

                    records.append({
                        'freq': freq_khz,
                        'start': t_start,
                        'end': t_end,
                        'name': clean_name
                    })
                    
                except ValueError:
                    continue

        # Ordina per frequenza (FONDAMENTALE per la ricerca binaria o sequenziale)
        records.sort(key=lambda x: x['freq'])

        print(f"Trovate {len(records)} stazioni valide (filtrate > 100kHz).")
        print(f"Scrittura file binario...")

        with open(full_output_path, 'wb') as binfile:
            for rec in records:
                # Prepara il nome: max 20 caratteri
                name_bytes = rec['name'].encode('utf-8')[:STATION_NAME_LEN]
                
                # CORREZIONE FONDAMENTALE: Padding con NULL (\x00) invece di spazi
                # Questo assicura che il C++ legga la stringa e si fermi al punto giusto
                name_padded = name_bytes.ljust(STATION_NAME_LEN, b'\x00')
                
                # Pack: H (2 byte freq), H (2 byte start), H (2 byte end), 20s (20 byte nome)
                binary_data = struct.pack('<HHH20s', 
                                          rec['freq'], 
                                          rec['start'], 
                                          rec['end'], 
                                          name_padded)
                binfile.write(binary_data)

        print(f"--- COMPLETATO ---")
        print(f"File creato: {OUTPUT_FILENAME}")
        print(f"Dimensione: {os.path.getsize(full_output_path)} bytes")

    except FileNotFoundError:
        print(f"ERRORE: File {INPUT_FILENAME} non trovato.")

if __name__ == "__main__":
    create_binary_db()