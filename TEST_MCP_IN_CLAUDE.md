# 🧪 TEST COMANDI PER CLAUDE DESKTOP

## ⚠️ IMPORTANTE: Prima di testare
1. **RIAVVIA Claude Desktop** dopo aver copiato la configurazione
2. Verifica che il file di config sia in: `~/.claude/claude_mcp_config.json`
3. Se alcuni server non funzionano, potrebbero mancare le API keys

## 📝 COMANDI DA COPIARE E INCOLLARE IN CLAUDE DESKTOP

### 1️⃣ **FILESYSTEM** ✅
```
Create a file /tmp/mcp_test.txt with content "MCP works!"
Read the file /tmp/mcp_test.txt
List all files in /tmp/ that start with mcp_
```

### 2️⃣ **GIT** ✅
```
Show the git status of /Users/erik/Desktop/claude-multiagent-system
Show the last 3 git commits
```

### 3️⃣ **MEMORY** ✅
```
Store this knowledge: "Test completed at [current time]"
Retrieve all stored knowledge
```

### 4️⃣ **FETCH** ✅
```
Fetch https://api.github.com/rate_limit
```

### 5️⃣ **SEQUENTIAL THINKING** ✅
```
Think step-by-step: How to implement authentication?
```

### 6️⃣ **TIME** ✅
```
What is the current Unix timestamp?
What day will it be in 30 days?
```

### 7️⃣ **EVERYTHING** ✅
```
Search for information about "MCP servers"
```

### 8️⃣ **SQLITE** ✅
```
Create a table "test_users" in /Users/erik/Desktop/claude-multiagent-system/data/test.db
Insert a user with name "Alice" and email "alice@test.com"
Query all users from the test_users table
```

### 9️⃣ **POSTGRES** ⚠️ (Richiede DATABASE_URL)
```
Se hai PostgreSQL configurato, imposta DATABASE_URL prima
```

### 🔟 **REDIS** ✅ (Se Redis è in esecuzione)
```
Test Redis connection on localhost:6379
Set key "mcp:test" to value "success"
Get value of key "mcp:test"
```

### 1️⃣1️⃣ **PUPPETEER** ✅
```
Take a screenshot of https://example.com
```

### 1️⃣2️⃣ **PLAYWRIGHT** ⚠️ (Potrebbe non essere visibile)
```
Se playwright-mcp non appare, verifica installazione globale
```

### 1️⃣3️⃣ **FIGMA** ⚠️ (Richiede FIGMA_TOKEN)
```
Richiede token API Figma nelle variabili d'ambiente
```

### 1️⃣4️⃣ **GITHUB** ⚠️ (Richiede GITHUB_TOKEN)
```
List repositories for user "modelcontextprotocol"
```

### 1️⃣5️⃣ **DOCKER** ⚠️ (Potrebbe non essere visibile)
```
List all Docker containers
```

### 1️⃣6️⃣ **NOTION** ⚠️ (Richiede NOTION_API_KEY)
```
Richiede API key di Notion nelle variabili d'ambiente
```

### 1️⃣7️⃣ **MULTI-AGENT** ✅
```
Query the mcp_system.db database for all agents
```

## 🔍 TEST RAPIDO PER VERIFICARE QUALI SERVER SONO ATTIVI

Incolla questo comando singolo in Claude Desktop:

```
Please test these MCP servers:
1. Create and read a file /tmp/quick_test.txt
2. Get current git status
3. Get current Unix timestamp
4. Create a SQLite table in /Users/erik/Desktop/claude-multiagent-system/data/test.db
```

## ✅ SERVER CHE DOVREBBERO FUNZIONARE SUBITO:
- Filesystem
- Git
- Memory
- Fetch
- Sequential Thinking
- Time
- Everything
- SQLite
- Multi-Agent

## ⚠️ SERVER CHE RICHIEDONO CONFIGURAZIONE:
- **PostgreSQL**: Serve DATABASE_URL
- **Redis**: Deve essere in esecuzione (`redis-server`)
- **Figma**: Serve FIGMA_TOKEN
- **GitHub**: Serve GITHUB_TOKEN
- **Notion**: Serve NOTION_API_KEY

## ❌ SERVER CHE POTREBBERO NON ESSERE VISIBILI:
- **Playwright**: Problema con installazione globale npm
- **Docker**: Problema con installazione globale npm

## 🚀 FIX PER SERVER NON FUNZIONANTI:

### Fix per Notion:
```bash
# Ottieni API key da https://www.notion.so/my-integrations
export NOTION_API_KEY="secret_xxxxx"
# Aggiungi al file di configurazione
```

### Fix per GitHub:
```bash
# Crea token su https://github.com/settings/tokens
export GITHUB_TOKEN="ghp_xxxxx"
```

### Fix per server npm globali non visibili:
```bash
# Reinstalla con percorso completo
npm install -g notion-mcp-server
npm install -g docker-mcp
npm install -g playwright-mcp
npm install -g figma-mcp

# Verifica percorsi
which notion-mcp-server
which docker-mcp
```

### Riavvia Claude Desktop dopo ogni modifica!

## 📊 RISULTATO ATTESO:
Su 17 server, dovresti vedere funzionare almeno 9-10 server base senza configurazione aggiuntiva.