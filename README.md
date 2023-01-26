![unilogo-2](https://user-images.githubusercontent.com/100310104/205032140-c5948459-de83-416f-9674-80c21668da7f.png)

# Progetto IoT Sensor Simulation "Powered By Fiware" - Corso di Big Data Management

## Struttura directory

Il progetto si articola nelle seguenti directory:
- *analysis* :
	- Dockerfile - istruzioni per il build dell'immagine
	- analysis.py - codice del container di analisi
	- requirements.txt - requisiti del container
	- average_values.json : valori medi da caricare sul DB
- *application* :
	- Dockerfile - istruzioni per il build dell'immagine
	- index.js - codice di back-end del container web App
	- dashboard.html - codice di front-end del container Web App
	- package.json
- *docker-compose* : 
	- docker-compose.yml : istruzioni per i container Fiware
	- dc.yml : istruzioni per i container sviluppati per il progetto
- *sensor* : 
	- Dockerfile - istruzioni per il build dell'immagine
	- sensor.py - codice del container sensore
	- requirements.txt - requisiti del container
- **services.sh** : script di gestione del progetto

## Sinossi

	./services.sh [OPZIONE]
	
	OPZIONI
	help            Mostra i comandi disponibili.
	create          Ferma i container. Inizia il pull delle immagini Fiware. Rimuove le build delle immagini personali.
	start           Ferma i container. Esegue il build delle immagini personali. Avvia i container.
	stop            Ferma i container.
	purge           Rimuove tutte le immagini ed i pull eseguiti per il progetto.
	
	ESEMPI
	./services create
	./services start
	./services stop

