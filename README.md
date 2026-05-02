# TEDexplore  
Explore and learn with us

TEDexplore è un progetto universitario che consiste nello sviluppo di un’app mobile dedicata alla formazione tramite talk TEDx.  
L’obiettivo è trasformare contenuti ispirazionali in **percorsi formativi strutturati e interattivi**, migliorando l’esperienza di apprendimento.

---

## 🎯 Obiettivo del progetto
Fornire un’esperienza formativa guidata e interattiva basata su contenuti TEDx, utilizzando un’architettura serverless semplice, scalabile e compatibile con i servizi AWS Academy.
I contenuti TEDx sono ampiamente disponibili online, ma risultano spesso frammentati e difficili da seguire in modo coerente.  

TEDexplore si propone di:
- Organizzare i talk in **percorsi tematici progressivi**
- Offrire un’esperienza di **apprendimento guidato**
- Integrare **quiz e test di valutazione**
- Migliorare la **scoperta dei contenuti (discovery)**

---

## 💡 Idea del servizio

L’app organizza i contenuti TEDx in percorsi formativi composti da:

- Video selezionati
- Quiz associati a ogni talk
- Test finale di verifica
- Ricerca avanzata (keyword, durata, anno, popolarità)

---

## 🏗️ Architettura

L’infrastruttura è progettata secondo un paradigma **serverless**, utilizzando:

- **AWS Lambda** – Business logic (percorsi, quiz, ricerca, statistiche)
- **Amazon API Gateway** – Interfaccia tra app mobile e backend
- **Firebase Authentication** – Gestione autenticazione utenti
- **Amazon S3** – Storage dei dataset TEDx
- **MongoDB** – Database applicativo

L’architettura combina servizi AWS e Firebase per garantire **scalabilità, flessibilità e semplicità di integrazione**, in particolare lato mobile.

---

## ⚙️ Gestione dei dati

Il sistema distingue due fasi principali:

### 🔄 Preprocessing
- Organizzazione e pulizia dei dati TEDx
- Supporto alla creazione dei percorsi formativi
- Supporto alla generazione dei quiz (es. tramite strumenti esterni)

### ⚡ Runtime
- Gestione delle richieste utente
- Ricerca e navigazione dei contenuti
- Raccolta delle statistiche di utilizzo

Questa separazione consente di ottimizzare le prestazioni e gestire in modo efficiente il carico applicativo.

---

## 📱 Funzionalità principali

- Percorsi formativi basati su talk TEDx
- Quiz di verifica alla fine dei contenuti
- Salvataggio dei progressi utente
- Ricerca avanzata dei contenuti
- Statistiche sull’apprendimento

---

## ⚠️ Criticità

- Dataset TEDx statico
- Aggiornamento dei contenuti manuale
- Creazione iniziale di percorsi e quiz non completamente automatizzata
- Complessità nella progettazione dell’esperienza utente

---

## 👥 Target

- Studenti
- Giovani professionisti
- Appassionati TEDx
- Docenti e formatori

---

## 📂 Struttura del repository

```(Da aggiornare con l’evoluzione del progetto)```

- `/backend` – Funzioni AWS Lambda e API
- `/frontend` – Codice dell’app mobile
- `/homeworks` - Presentazioni pdf con i 4 homework aggiornati
- `/docs` – Documentazione e altri materiali del progetto

---

## 🚀 Evoluzioni future

### ⚙️ Data & Automazione
- Automazione della generazione di percorsi e quiz
- Miglioramento della discovery dei contenuti

### 📈 Prodotto
- Espansione del catalogo TEDx

### 🎨 User Experience
- Ottimizzazione dell’esperienza utente

---

## 👨‍💻 Autore

Progetto sviluppato da @szinesi1 per il corso universitario “Piattaforme Cloud e Applicazioni Mobili” del corso di laurea triennale in Ingegneria Informatica.

---

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.  
Consulta il file `LICENSE` per maggiori informazioni.
