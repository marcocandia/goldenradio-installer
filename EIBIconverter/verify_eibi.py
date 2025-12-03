import struct
import os

# === CONFIGURAZIONE ===
INPUT_FILENAME = 'EIBI.DAT'
RECORD_SIZE = 26  # 2 (Freq) + 2 (Start) + 2 (End) + 20 (Name)

def minutes_to_hhmm(minutes):
    """Riconverte i minuti totali in formato HH:MM"""
    hh = minutes // 60
    mm = minutes % 60
    return f"{hh:02d}:{mm:02d}"

def verify_database():
    print(f"\n--- VERIFICA INTEGRITÀ {INPUT_FILENAME} ---")

    if not os.path.exists(INPUT_FILENAME):
        print(f"ERRORE: Il file {INPUT_FILENAME} non esiste.")
        return

    file_size = os.path.getsize(INPUT_FILENAME)
    print(f"Dimensione file: {file_size} bytes")

    # Controllo preliminare dimensione
    if file_size % RECORD_SIZE != 0:
        print(f"ATTENZIONE: La dimensione del file NON è un multiplo di {RECORD_SIZE}!")
        print("Il file potrebbe essere corrotto o il formato errato.")
    else:
        print(f"Struttura file corretta (Multiplo di {RECORD_SIZE}).")

    total_records = file_size // RECORD_SIZE
    print(f"Totale stazioni stimate: {total_records}")
    print("-" * 60)
    print(f"{'FREQ (kHz)':<12} | {'ORARIO UTC':<15} | {'NOME STAZIONE'}")
    print("-" * 60)

    try:
        with open(INPUT_FILENAME, 'rb') as f:
            count = 0
            # Leggiamo i primi 20 record per vedere se hanno senso
            while count < 20:
                chunk = f.read(RECORD_SIZE)
                if not chunk:
                    break

                # Unpack dei dati binari
                # < = Little Endian
                # H = unsigned short (2 bytes) -> Freq, Start, End
                # 20s = stringa di 20 bytes -> Nome
                data = struct.unpack('<HHH20s', chunk)

                freq = data[0]
                start_time = minutes_to_hhmm(data[1])
                end_time = minutes_to_hhmm(data[2])
                
                # Pulizia nome: decodifica byte -> stringa e toglie spazi/null
                raw_name = data[3]
                try:
                    name = raw_name.decode('utf-8', errors='ignore').strip('\x00').strip()
                except:
                    name = "[Errore Decodifica Nome]"

                print(f"{freq:<12} | {start_time} - {end_time}   | {name}")
                count += 1
            
            print("...")
            print(f"(Altri {total_records - 20} record non visualizzati)")

    except Exception as e:
        print(f"ERRORE durante la lettura: {e}")

if __name__ == "__main__":
    verify_database()