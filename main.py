import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, time
import os
import asyncio
from telegram import Bot

BASSANO = "Monitor?placeId=602&arrivals=False" 
PORTO_MARGHERA = "Monitor?placeId=3004&arrivals=False"
MESTRE = "Monitor?placeId=3002&arrivals=False"
VENEZIA_SANTA_LUCIA = "Monitor?placeId=3009&arrivals=False"

Treni_Bassano = []
Treni_Porto_Marghera = []
Treni_Mestre = []
Treni_Venezia = []


# MODIFICA QUESTA FUNZIONE COSÌ:
async def send_telegram_alert(messaggio):
    # Python cercherà queste variabili nel "sistema" di GitHub
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if token and chat_id and messaggio:
        try:
            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=messaggio)
            print("Messaggio inviato con successo!")
        except Exception as e:
            print(f"Errore durante l'invio: {e}")
    else:
        print("Errore: Token o Chat ID non trovati nelle variabili d'ambiente.")


def take_information(Treni, todo, stazione, stazione_arrivo):
    if todo:
        righe = todo.find_all('tr')

        for riga in righe:

            destinazione = riga.find('td', {'class': 'Stazione_classtd marquee'})
            if destinazione is not None:
                destinazione = destinazione.get_text(strip=True)
                #print("Destinazione: " + destinazione)

            id_treno = riga.find('td', {'id': 'RTreno'})
            if id_treno is not None:
                id_treno = id_treno.get_text(strip=True)
                #print("Id treno: " + id_treno)
                

            orario = riga.find('td', {'class': 'Orario_classtd'})
            if orario is not None:
                orario = orario.get_text(strip=True)
                #print("Orario partenza: " +orario)


            ritardo = riga.find('td', {'class': 'Ritardo_classtd'})
            if ritardo is not None:
                ritardo = ritardo.get_text(strip=True)
                #rint("Ritardo: " + ritardo)


            binario = riga.find('td', {'class': 'marquee Binario_classtd'})
            if binario is not None:
                binario = binario.get_text(strip=True)
                #print("Binario: " + binario + "\n")

            treno = {
                    "stazione": "",
                    "id_treno": "",
                    "destinazione" : "",
                    "orario_partenza" : "",
                    "Ritardo": "",
                    "Binario" : ""
                }
            
            treno['stazione'] = stazione
            treno['id_treno'] = id_treno
            treno['destinazione'] = destinazione 
            treno['orario_partenza'] = orario
            treno['Ritardo'] = ritardo
            treno['Binario'] = binario

            ritardo_pulito = ritardo if (ritardo and ritardo.isdigit()) else "0"

            if (destinazione.upper() in stazione_arrivo and ( "CANCELLATO" in ritardo.upper() or "SOPRESSO" in ritardo.upper() or int(ritardo_pulito) > 3 )):
                #Treni.append(treno)

                msg = f"⚠️ ALLERTA TRENO {id_treno}\nDa: {stazione}\nPer: {destinazione}\nPartenza: {orario}\nStato: {ritardo}\nBinario: {binario}"
                # Usiamo asyncio per inviare il messaggio
                asyncio.run(send_telegram_alert(msg))
                #Treni.append(treno)

                
        #with open("bassano.json", "w", encoding="utf-8") as f:
        #   json.dump(Treni, f, indent=4, ensure_ascii=False)


def check_orario_consentito(ora_inizio, minuti_inizio, ora_fine, minuti_fine):
    adesso = datetime.now()
    
    # 1. Controllo Giorno (Lunedì=0, Giovedì=3)
    is_giorno_giusto = 0 <= adesso.weekday() <= 3
    
    # 2. Controllo Orario (Molto più chiaro!)
    ora_attuale = adesso.time()
    inizio = time(ora_inizio, minuti_inizio)  # Rappresenta le 06:20:00
    fine = time(ora_fine, minuti_fine)    # Rappresenta le 13:00:00
    
    is_orario_giusto = inizio <= ora_attuale <= fine
    
    return is_giorno_giusto and is_orario_giusto


def start():

    #Partenze da Bassano
    if (check_orario_consentito(6, 20, 13, 0)):#decido quando può partire la ricerca 
        r = requests.get("https://iechub.rfi.it/ArriviPartenze/ArrivalsDepartures/" + BASSANO)#prendo l'url contenente ik tabellone
        content = r.text#lo converto in un testo
        soup = BeautifulSoup(content, 'html.parser')
        todo = soup.find('tbody')#prendo solamente ciò che mi interessa
        take_information(Treni_Bassano, todo, "BASSANO DEL GRAPPA", "VENEZIA S.LUCIA")#faccio prendere le informazioni che mi interessano



    #Partenze da Mestre
    if (check_orario_consentito(13, 00, 18, 00)):
        r = requests.get("https://iechub.rfi.it/ArriviPartenze/ArrivalsDepartures/" + MESTRE)
        content = r.text
        soup = BeautifulSoup(content, 'html.parser')
        todo = soup.find('tbody')
        take_information(Treni_Mestre, todo, "MESTRE", "BASSANO DEL GRAPPA")

    #Partenze da Venezia_porto_margera
    if (check_orario_consentito(13, 00, 18, 00)):
        r = requests.get("https://iechub.rfi.it/ArriviPartenze/ArrivalsDepartures/" + PORTO_MARGHERA)
        content = r.text
        soup = BeautifulSoup(content, 'html.parser')
        todo = soup.find('tbody')
        take_information(Treni_Porto_Marghera, todo, "VENEZIA PORTO MARGHERA", "BASSANO DEL GRAPPA")


    #Partenze da Venezia_santa_lucia 
    if (check_orario_consentito(13, 00, 18, 00)):
        r = requests.get("https://iechub.rfi.it/ArriviPartenze/ArrivalsDepartures/" + VENEZIA_SANTA_LUCIA)
        content = r.text
        soup = BeautifulSoup(content, 'html.parser')
        todo = soup.find('tbody')
        take_information(Treni_Venezia, todo, "VENEZIA SANTA LUCIA", "BASSANO DEL GRAPPA")

if __name__ == "__main__":
    asyncio.run(send_telegram_alert("ti invio un mess"))
    start()