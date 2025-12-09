import csv
import struct
import sys

# CONFIGURAZIONE
INPUT_FILE = 'sked-b25.csv'  # Scarica questo da eibispace.de
OUTPUT_FILE = 'EIBI.BIN'

def parse_time(time_str):
    # Formato tipico: "0000-0100" o "1230-1400"
    try:
        sh = int(time_str[0:2])
        sm = int(time_str[2:4])
        eh = int(time_str[5:7])
        em = int(time_str[7:9])
        return sh, sm, eh, em
    except:
        return 0, 0, 23, 59 # Default tutto il giorno se errore

entries = []

print(f"Lettura di {INPUT_FILE}...")

try:
    with open(INPUT_FILE, mode='r', encoding='latin-1', errors='replace') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            if len(row) < 5: continue
            
            # Eibi CSV format: KHz;Time;Days;ITU;Station;...
            try:
                freq_khz = int(float(row[0])) # Colonna 0: Frequenza
                time_str = row[1]             # Colonna 1: Orario
                name = row[4]                 # Colonna 4: Nome Stazione
                
                # Filtra frequenze non gestibili (es. > 30MHz o 0)
                if freq_khz <= 0 or freq_khz > 30000: continue

                sh, sm, eh, em = parse_time(time_str)
                
                entries.append({
                    'freq': freq_khz,
                    'sh': sh, 'sm': sm,
                    'eh': eh, 'em': em,
                    'name': name
                })
            except ValueError:
                continue

    # ORDINAMENTO FONDAMENTALE PER LA RICERCA BINARIA
    print("Ordinamento dati...")
    entries.sort(key=lambda x: x['freq'])

    print(f"Scrittura di {len(entries)} stazioni su {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'wb') as f:
        for e in entries:
            # Tronca o Riempi il nome a 25 caratteri + terminatore (Totale 26 byte)
            name_bytes = e['name'].encode('utf-8')[:25]
            
            # Struttura Binaria (Little Endian):
            # H = uint16 (Freq)
            # b = int8 (ore/minuti)
            # 26s = stringa 26 char
            # Totale = 2 + 1+1+1+1 + 26 = 32 Byte esatti
            data = struct.pack('<Hbbbb26s', 
                               e['freq'], 
                               e['sh'], e['sm'], e['eh'], e['em'], 
                               name_bytes)
            f.write(data)

    print("Fatto! Ora carica EIBI.BIN sulla radio tramite il sito web.")

except FileNotFoundError:
    print(f"Errore: File {INPUT_FILE} non trovato. Scaricalo da http://eibispace.de/dx/")