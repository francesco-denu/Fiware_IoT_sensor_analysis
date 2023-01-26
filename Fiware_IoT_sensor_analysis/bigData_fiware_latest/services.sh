#!/bin/bash

dockerCmd="docker compose"
if (( $# == 2 )); then
    dockerCmd="docker-compose"
fi

if (( $# < 1 )); then
	echo "Illegal number of parameters"
	echo "usage: services [help|create|start|stop|purge]"
	exit 1
fi

getHeartbeat(){
	eval "response=$(docker run --network fiware_default --rm curlimages/curl -s -o /dev/null -w "%{http_code}" "$1")"
}

waitForMongo () {
	echo -e "\n⏳ Waiting for \033[1;34mMongoDB\033[0m to be available\n"
	while ! [ `docker inspect --format='{{.State.Health.Status}}' db-mongo` == "healthy" ]
	do
		sleep 1
	done
}

waitForOrion () {
	echo -e "\n⏳ Waiting for \033[1;33mOrion\033[0m to be available... usually no more then 5 attempts\n\n"

	while ! [ `docker inspect --format='{{.State.Health.Status}}' fiware-orion` == "healthy" ]
	do
	  echo -e "Context Broker HTTP state: " `curl -s -o /dev/null -w %{http_code} 'http://localhost:1026/version'` " (waiting for 200)"
	  sleep 5
	done
}

loadData () {
	echo -e "Creating \033[1;34mMongoDB\033[0m collections: \033[0;33mmeasurements\033[0m, \033[0;33mmeans\033[0m ..."
	docker exec  db-mongo mongo --eval '
	conn = new Mongo();
	db = conn.getDB("orion");
	db.createCollection("measurements");
	db.createCollection("means");' > /dev/null
	echo -e "\033[1;32mdone\033[0m"
}

sium(){
	echo -e -n " \033[1;31mSiuuuuuum! \033[0m"
	echo -e -n "\033[1G"
	sleep 1
	echo -e -n " \033[1;36mSiuuuuuum! \033[0m"
	echo -e -n "\033[1G"
	sleep 1
	echo -e -n " \033[1;38mSiuuuuuum! \033[0m"
	echo -e -n "\033[1G"
	sleep 1
	echo -e " \033[5;33mSiuuuuuum! \033[0m"
}

addDatabaseIndex () {
	echo -e "Createing \033[1;34mMongoDB\033[0m database indexes ..."
	docker exec  db-mongo mongo --eval '
	conn = new Mongo();
	db = conn.getDB("orion");
	db.createCollection("entities");
	db.entities.createIndex({"_id.servicePath": 1, "_id.id": 1, "_id.type": 1}, {unique: true});
	db.entities.createIndex({"_id.type": 1});
	db.entities.createIndex({"_id.id": 1});' > /dev/null
	echo -e "\033[1;32mdone\033[0m"
}

stoppingContainers () {
	CONTAINERS=$(docker ps --filter "label=org.fiware=tutorial" -aq)

	if [[ "$(docker inspect -f '{{.State.Running}}' sensor 2>/dev/null)" == "true" ]]
	then
		echo -e "Stopping \033[1;31msensor\033[0m container"
  		docker rm -f sensor 1> /dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ "$(docker inspect -f '{{.State.Running}}' analysis 2>/dev/null)" == "true" ]]
	then
		echo -e "Stopping \033[1;35mAnalysis\033[0m container"
  		docker rm -f analysis 1> /dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ "$(docker inspect -f '{{.State.Running}}' application 2>/dev/null)" == "true" ]]
	then
		echo -e "Stopping \033[1;36mWeb App\033[0m container"
  		docker rm -f application 1> /dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ -n $CONTAINERS ]]; then
		echo -e "Stopping \033[1;33mFiware\033[0m containers"
		docker rm -f $CONTAINERS 1>/dev/null|| true
		echo -e "\033[1;32mdone\033[0m"
	fi

	VOLUMES=$(docker volume ls -qf dangling=true)
	if [[ -n $VOLUMES ]]; then
		echo "Removing old volumes"
		docker volume rm $VOLUMES 1>/dev/null|| true
		echo -e "\033[1;32mdone\033[0m"
	fi

	NETWORKS=$(docker network ls  --filter "label=org.fiware=tutorial" -q)
	if [[ -n $NETWORKS ]]; then
		echo "Removing tutorial networks"
		docker network rm $NETWORKS 1>/dev/null|| true
		echo -e "\033[1;32mdone\033[0m"
	fi
}

displayServices () {
	echo ""
	echo -e "\033[5;31mSensor\033[0m                     --------------"
	echo -e "\033[5;35mAnalysis Server \033[0m           localhost:5050/notification"
	echo -e "                           localhost:5050/measure"
	echo -e "\033[5;33mOrion Contex Broker\033[0m        localhost:1026"
	echo -e "\033[5;34mMongo-DB\033[0m                   localhost:27017"
	echo -e "\033[5;36mNode.js Web APP\033[0m            localhost:3000"
	echo ""
}

removingPersonal(){
	if [[ "$(docker images -q docker-compose-sensor 2>/dev/null)" != "" ]]
	then
		echo -e "Removing \033[1;31msensor\033[0m image."
		docker image rm -f docker-compose-sensor 1>/dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ "$(docker images -q docker-compose-analysis 2>/dev/null)" != "" ]]
	then
		echo -e "Removing \033[1;35mAnalysis\033[0m image."
		docker image rm -f docker-compose-analysis 1>/dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ "$(docker images -q docker-compose-app 2>/dev/null)" != "" ]]
	then
		echo -e "Removing \033[1;36mWeb App\033[0m image."
		docker image rm -f docker-compose-app 1>/dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi
}

removingFiware(){
		if [[ "$(docker images -q fiware/orion-ld 2>/dev/null)" != "" ]]
	then
		echo -e "Removing \033[1;33mOrion Contex Broker\033[0m image."
		docker image rm -f $(docker images -q fiware/orion-ld) 1>/dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi

	if [[ "$(docker images -q mongo 2>/dev/null)" != "" ]]
	then
		echo -e "Removing \033[1;34mMongo-DB\033[0m image."
		docker image rm -f $(docker images -q mongo) 1>/dev/null
		echo -e "\033[1;32mdone\033[0m"
	fi
}

command="$1"
case "${command}" in
	"help")
        echo "usage: services [help|create|start|stop|purge]"
		echo ""
		echo "help   : Mostra i comandi disponibili."
		echo "create : Ferma i container. Inizia il pull delle immagini Fiware. Rimuove le build delle immagini personali."
		echo "start  : Ferma i container. Esegue il build delle immagini personali. Avvia i container."
		echo "stop   : Ferma i container."
		echo "purge  : Rimuove tutte le immagini ed i pull eseguiti per il progetto."
        ;;
    "start")
		stoppingContainers # fermiamo i container attivit
		echo -e "Starting containers:   \033[1;33mOrion\033[0m and a \033[1;34mMongoDB\033[0m database."
		echo ""
		${dockerCmd} -f docker-compose/docker-compose.yml up -d --remove-orphans --renew-anon-volumes # avviamo i container Fiware
		waitForMongo # aspettiamo che Mongo sia online
		loadData # creiamo le collection e carichiamo i dati dei valori medi
		addDatabaseIndex # aggiungiamo le collection di orion e gli indici
		waitForOrion # aspettiamo orion sia online
		echo -e "Starting containers:    \033[1;35mAnalysis\033[0m, \033[1;31mSensor\033[0m, \033[1;36mNode.js Web APP\033[0m"
		${dockerCmd} -f docker-compose/dc.yml up -d --renew-anon-volumes # avviamo i container realizzati per il progetto
		displayServices # mostriamo i servizi disponibili
		;;
	"stop")
		stoppingContainers
		;;
	"purge")
		echo -e "\033[5;31mPurge started...\033[0m"
		stoppingContainers
		removingPersonal
		removingFiware
		;;
	"sium")
		sium
		;;
	"create")
		stoppingContainers # ferma i container
		echo "Pulling Docker images and deleting builded images."
		docker pull curlimages/curl
		${dockerCmd} -f docker-compose/docker-compose.yml pull # fa il pull delle immagini orion
		removingPersonal # rimuove le immagini personali, utile se si sono fatti cambiamenti al codice
		;;
	*)
		echo "Command not Found."
		echo "usage: services [help|create|start|stop|purge]"
		exit 127;
		;;
esac
