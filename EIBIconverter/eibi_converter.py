import csv
import struct
import os

# === CONFIGURAZIONE ===
INPUT_FILENAME = 'goldenradio-installer\eibiconverter\sked-b25.csv'  # Cambia questo con il nome del file scaricato da eibispace
OUTPUT_FILENAME = 'EIBI.DAT'
STATION_NAME_LEN = 20            # Lunghezza fissa del nome stazione (byte)

# Struttura Binaria per ESP32 (26 bytes totale):
# - FreqStart (2 bytes, uint16)
# - StartTime (2 bytes, uint16 minutes)
# - EndTime   (2 bytes, uint16 minutes)
# - Name      (20 bytes, char string)

def time_to_minutes(hhmm_str):
    """Converte stringa HHMM in minuti dalla mezzanotte."""
    try:
        hh = int(hhmm_str[0:2])
        mm = int(hhmm_str[2:4])
        return hh * 60 + mm
    except:
        return 0

def create_binary_db():
    print(f"--- ELABORAZIONE {INPUT_FILENAME} ---")
    
    records = []
    count = 0
    skipped = 0

    try:
        with open(INPUT_FILENAME, mode='r', encoding='latin-1', errors='ignore') as csvfile:
            # EIBI usa il punto e virgola come separatore
            reader = csv.reader(csvfile, delimiter=';')
            
            for row in reader:
                # Salta righe vuote o commenti
                if not row or len(row) < 5:
                    continue
                
                # EIBI Format tipico:
                # KHz;TimeStart;TimeEnd;Days;ITU;Station;Lng;Target;Transmitter
                # 0   1         2       3    4   5       6   7      8
                
                try:
                    freq_khz = int(float(row[0])) # A volte sono float
                    time_start_str = row[1]
                    time_end_str = row[2]
                    station_name = row[5]
                    
                    # Filtra frequenze impossibili (0 o > 30MHz se vuoi limitare)
                    if freq_khz <= 0 or freq_khz > 30000:
                        skipped += 1
                        continue

                    t_start = time_to_minutes(time_start_str)
                    t_end = time_to_minutes(time_end_str)
                    
                    # Gestione nome stazione (pulisci e codifica ASCII)
                    # Rimuoviamo caratteri strani per compatibilità
                    clean_name = station_name.encode('ascii', 'ignore').decode('ascii')
                    
                    # Aggiungi alla lista per l'ordinamento
                    records.append({
                        'freq': freq_khz,
                        'start': t_start,
                        'end': t_end,
                        'name': clean_name
                    })
                    
                except ValueError:
                    # Intestazioni o dati sporchi
                    skipped += 1
                    continue

        # --- ORDINAMENTO ---
        # Fondamentale per la Binary Search sull'ESP32
        print("Ordinamento dei dati per frequenza...")
        records.sort(key=lambda x: x['freq'])

        # --- SCRITTURA BINARIA ---
        print(f"Scrittura di {OUTPUT_FILENAME}...")
        
        with open(OUTPUT_FILENAME, 'wb') as binfile:
            for rec in records:
                # Pack dei dati:
                # < = Little Endian (standard ESP32)
                # H = unsigned short (2 bytes)
                # 20s = stringa di 20 bytes
                
                # Tronca o riempi il nome a 20 caratteri
                name_bytes = rec['name'].ljust(STATION_NAME_LEN)[:STATION_NAME_LEN].encode('utf-8')
                
                binary_data = struct.pack('<HHH20s', 
                                          rec['freq'], 
                                          rec['start'], 
                                          rec['end'], 
                                          name_bytes)
                binfile.write(binary_data)
                count += 1

        print(f"--- COMPLETATO ---")
        print(f"Record scritti: {count}")
        print(f"Record saltati: {skipped}")
        print(f"Dimensione file: {os.path.getsize(OUTPUT_FILENAME) / 1024:.2f} KB")
        print(f"Copia '{OUTPUT_FILENAME}' nella cartella 'data' del tuo progetto PlatformIO.")

    except FileNotFoundError:
        print(f"ERRORE: Il file {INPUT_FILENAME} non è stato trovato.")

if __name__ == "__main__":
    create_binary_db()