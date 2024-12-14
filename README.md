# RAT
Remote Monitoring Client (Remote Access Trojan)
Descrizione
Questo progetto rappresenta un client Python avanzato progettato per la gestione remota di dispositivi. Il programma consente l'esecuzione di diverse funzionalità in modo discreto, tra cui:

Keylogging: Registra i tasti premuti dall'utente e li invia al server configurato.
Cattura di schermate: Effettua screenshot periodici del dispositivo e li trasmette al server.
Gestione di comandi remoti: Permette di eseguire comandi shell inviati dal server.
Raccolta di informazioni di sistema: Fornisce informazioni utili sul dispositivo, come il nome utente e la posizione approssimativa.
Connessione automatica: Garantisce la riconnessione continua al server in caso di disconnessione.
Avvio automatico: Configurabile per avviarsi automaticamente all'accesso del sistema operativo.
Funzionamento
Il client si connette a un server remoto attraverso diverse porte TCP per gestire funzionalità specifiche. Ogni funzione è implementata in modo modulare per garantire scalabilità e affidabilità.

Le principali porte di comunicazione sono:

12464: Trasferimento degli screenshot.
12465: Esecuzione di comandi remoti.
12466: Invio di informazioni di sistema.
12467: Trasmissione dei file di keylogging.
Scopo Didattico
Questo progetto è pensato esclusivamente per scopi educativi e di apprendimento. È progettato per studiare la comunicazione client-server, la sicurezza informatica, e l'automazione di funzioni su reti remote. L'uso non autorizzato o illegale di questo software è severamente vietato e contrario alle leggi vigenti.

Requisiti
Python 3.7 o superiore
Moduli Python aggiuntivi:
socket, subprocess, threading, struct
os, sys, time, getpass
pyautogui, cv2, numpy (per la cattura di schermate)
pynput (per il keylogger)
geopy (per la localizzazione geografica)
Esecuzione
Configura l'IP del server remoto nel file client.py.

Compila il client in un eseguibile utilizzando PyInstaller:
python -m PyInstaller --onefile --noconsole client.py

Avvia il client per stabilire la connessione al server.
Avvertenze
L'utilizzo del software deve essere conforme alle normative locali e internazionali. L'autore non è responsabile per un uso improprio o illegale del programma.

![Screenshot del progetto](images/screenshot.png)

