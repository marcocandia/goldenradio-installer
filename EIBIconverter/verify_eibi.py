# import struct
# import os

# # === CONFIGURAZIONE ===
# INPUT_FILENAME = 'EIBI.DAT'
# RECORD_SIZE = 26  # 2 (Freq) + 2 (Start) + 2 (End) + 20 (Name)

# def minutes_to_hhmm(minutes):
#     """Riconverte i minuti totali in formato HH:MM"""
#     hh = minutes // 60
#     mm = minutes % 60
#     return f"{hh:02d}:{mm:02d}"

# def verify_database():
#     print(f"\n--- VERIFICA INTEGRITÀ {INPUT_FILENAME} ---")

#     if not os.path.exists(INPUT_FILENAME):
#         print(f"ERRORE: Il file {INPUT_FILENAME} non esiste.")
#         return

#     file_size = os.path.getsize(INPUT_FILENAME)
#     print(f"Dimensione file: {file_size} bytes")

#     # Controllo preliminare dimensione
#     if file_size % RECORD_SIZE != 0:
#         print(f"ATTENZIONE: La dimensione del file NON è un multiplo di {RECORD_SIZE}!")
#         print("Il file potrebbe essere corrotto o il formato errato.")
#     else:
#         print(f"Struttura file corretta (Multiplo di {RECORD_SIZE}).")

#     total_records = file_size // RECORD_SIZE
#     print(f"Totale stazioni stimate: {total_records}")
#     print("-" * 60)
#     print(f"{'FREQ (kHz)':<12} | {'ORARIO UTC':<15} | {'NOME STAZIONE'}")
#     print("-" * 60)

#     try:
#         with open(INPUT_FILENAME, 'rb') as f:
#             count = 0
#             # Leggiamo i primi 20 record per vedere se hanno senso
#             while count < 20:
#                 chunk = f.read(RECORD_SIZE)
#                 if not chunk:
#                     break

#                 # Unpack dei dati binari
#                 # < = Little Endian
#                 # H = unsigned short (2 bytes) -> Freq, Start, End
#                 # 20s = stringa di 20 bytes -> Nome
#                 data = struct.unpack('<HHH20s', chunk)

#                 freq = data[0]
#                 start_time = minutes_to_hhmm(data[1])
#                 end_time = minutes_to_hhmm(data[2])
                
#                 # Pulizia nome: decodifica byte -> stringa e toglie spazi/null
#                 raw_name = data[3]
#                 try:
#                     name = raw_name.decode('utf-8', errors='ignore').strip('\x00').strip()
#                 except:
#                     name = "[Errore Decodifica Nome]"

#                 print(f"{freq:<12} | {start_time} - {end_time}   | {name}")
#                 count += 1
            
#             print("...")
#             print(f"(Altri {total_records - 20} record non visualizzati)")

#     except Exception as e:
#         print(f"ERRORE durante la lettura: {e}")

# if __name__ == "__main__":
#     verify_database()


import struct
import os

# === CONFIGURAZIONE ===
FILENAME = 'EIBI.DAT'
# Struttura: 2 byte Freq + 2 byte Start + 2 byte End + 24 byte Nome = 30 bytes
RECORD_SIZE = 30 
NAME_LEN = 24

def minutes_to_hhmm(mins):
    """Converte minuti totali in stringa HH:MM"""
    h = mins // 60
    m = mins % 60
    return f"{h:02d}:{m:02d}"

def verify_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, FILENAME)

    if not os.path.exists(full_path):
        print(f"ERRORE: File {FILENAME} non trovato.")
        return

    file_size = os.path.getsize(full_path)
    
    # Verifica integrità di base
    if file_size % RECORD_SIZE != 0:
        print(f"ATTENZIONE: La dimensione del file ({file_size}) non è multipla di {RECORD_SIZE}!")
        print("Il file potrebbe essere corrotto o generato con parametri diversi.")
    
    num_records = file_size // RECORD_SIZE
    
    print(f"\n--- VERIFICA DATABASE EIBI ---")
    print(f"File: {FILENAME}")
    print(f"Dimensione: {file_size} bytes")
    print(f"Numero Record: {num_records}")
    print(f"Struttura Record: {RECORD_SIZE} bytes (Freq 2 + Time 4 + Name {NAME_LEN})")
    print("-" * 70)
    print(f"{'FREQ (kHz)':<12} {'TIME (UTC)':<15} {'STATION NAME'}")
    print("-" * 70)

    with open(full_path, 'rb') as f:
        count = 0
        while True:
            data = f.read(RECORD_SIZE)
            if len(data) != RECORD_SIZE:
                break
                
            # Unpack secondo la nuova struttura:
            # <  : Little Endian
            # H  : uint16 (Frequenza)
            # H  : uint16 (Start Time)
            # H  : uint16 (End Time)
            # 24s: Stringa 24 char (Nome)
            try:
                freq, start, end, name_bytes = struct.unpack('<HHH24s', data)
                
                # Pulisci il nome (decodifica e rimuovi padding null/spazi)
                name = name_bytes.decode('utf-8', errors='replace').strip('\x00').strip()
                
                time_str = f"{minutes_to_hhmm(start)}-{minutes_to_hhmm(end)}"
                
                # Stampa i primi 20 record, poi salta, poi stampa gli ultimi 5
                if count < 20:
                    print(f"{freq:<12} {time_str:<15} {name}")
                elif count == 20:
                    print("...")
                    print(f"... (saltati {num_records - 25} record) ...")
                    print("...")
                    # Salta alla fine per verificare gli ultimi record
                    # (utile per vedere se l'allineamento regge fino in fondo)
                    seek_pos = (num_records - 5) * RECORD_SIZE
                    if seek_pos > f.tell():
                        f.seek(seek_pos)
                        count = num_records - 6
                elif count >= num_records - 5:
                    print(f"{freq:<12} {time_str:<15} {name}")

                count += 1

            except struct.error as e:
                print(f"Errore di spacchettamento al record {count}: {e}")
                break

    print("-" * 70)
    print("Verifica completata.")

if __name__ == "__main__":
    verify_db()