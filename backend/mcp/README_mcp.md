# TEDexplore MCP Server — Homework 3

Server MCP che espone i dati di TEDexplore (MongoDB Atlas) come tool
utilizzabili da un assistente AI, incluso `get_watch_next` collegato
alla stessa logica della Lambda `Get_Watch_Next_by_Idx`.

## File nella cartella

- `server.py` — il server MCP (tool: `get_watch_next`, `search_by_tag`,
  `search_by_speaker`, `get_talk`)
- `client_ollama.py` — client che collega un modello Ollama locale al
  server, lasciando che sia l'LLM a decidere quando chiamare i tool
- `requirements.txt` — dipendenze Python

## Come farlo girare

1. Installa Ollama (ollama.com) e scarica un modello:
   ```
   ollama pull llama3.2:3b
   ```

2. Installa le dipendenze Python:
   ```
   pip install -r requirements.txt
   ```

3. Imposta la connection string di MongoDB Atlas (la stessa usata
   dalle Lambda):
   ```
   # Mac/Linux
   export MONGO_URI="mongodb+srv://<user>:<password>@<cluster>/?appName=<app>"

   # Windows (cmd)
   set MONGO_URI=mongodb+srv://<user>:<password>@<cluster>/?appName=<app>
   ```

4. Avvia il server (terminale 1, lascialo aperto):
   ```
   python server.py
   ```

5. In un SECONDO terminale, avvia il client:
   ```
   python client_ollama.py
   ```

6. L'output nel terminale del client (lista tool, chiamata al tool,
   risposta finale) è lo screenshot da usare nella slide MCP della
   presentazione.

## Note

- Nessun certificato SSL: gira in HTTP puro su `127.0.0.1`, sufficiente
  per un test/demo locale.
- La connection string NON va mai scritta nel codice o committata su
  GitHub: si legge solo dalla variabile d'ambiente `MONGO_URI`.