# TEDexplore

TEDexplore è un progetto universitario che consiste nello sviluppo di un’app mobile dedicata alla formazione tramite talk TEDx.  
L’app offre percorsi tematici, quiz interattivi, statistiche personalizzate e salvataggio dei progressi.

## 🎯 Obiettivo del progetto
Fornire un’esperienza formativa guidata e interattiva basata su contenuti TEDx, utilizzando un’architettura serverless semplice, scalabile e compatibile con i servizi AWS Academy.

## 🏗️ Architettura
L’infrastruttura è completamente serverless e utilizza:
- **AWS Lambda** – Business logic (percorsi, quiz, statistiche, ricerca)
- **Amazon API Gateway** – Interfaccia tra app mobile e backend
- **Amazon Cognito** – Autenticazione e gestione utenti
- **Amazon S3** – Storage dei dataset TEDx
- **MongoDB** – Database principale dell’app

## 📱 Funzionalità principali
- Percorsi formativi basati su talk TEDx
- Quiz di verifica alla fine dei contenuti
- Salvataggio dei progressi dell’utente
- Ricerca dei contenuti
- Statistiche sull’apprendimento

## 📂 Struttura del repository
*(Da aggiornare quando aggiungerai il codice)*  
- `/backend` – Funzioni Lambda e API  
- `/frontend` – Codice dell’app mobile  
- `/docs` – Documentazione del progetto  

## 👥 Autori
Progetto sviluppato da @szinesi1 per il corso universitario “Piattaforme Cloud e Applicazioni Mobili” del corso di laurea in Ingegneria Informatica.

## 📄 Licenza
Questo progetto è distribuito sotto licenza MIT.  
Consulta il file `LICENSE` per maggiori informazioni.
