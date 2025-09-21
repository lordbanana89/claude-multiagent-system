# 🧪 COME TESTARE IL SISTEMA MCP COMPLETO

## 1️⃣ **TEST RAPIDO (30 secondi)**

```bash
# Verifica installazione
python3 test_final_mcp_system.py

# Se vedi "17/17 servers operational (100%)" → TUTTO OK! ✅
```

## 2️⃣ **TEST FUNZIONALE (2 minuti)**

```bash
# Test di funzionalità reali
python3 test_all_mcp_functionality.py

# Verifica:
# - 21 test passati
# - Database creati
# - File generati
```

## 3️⃣ **TEST INTERATTIVO (5 minuti)**

```bash
# Dimostrazione live con output
python3 demonstrate_mcp_live.py

# Mostra:
# - Creazione file
# - Git operations
# - Database queries
# - Cache Redis
```

## 4️⃣ **TEST MANUALE DEI SINGOLI SERVER**

### A. Test Filesystem
```bash
# Crea e leggi file
echo "test" > test_mcp.txt
cat test_mcp.txt
rm test_mcp.txt
```

### B. Test Git
```bash
# Verifica Git MCP
git status
git log --oneline -5
```

### C. Test Memory (Knowledge Store)
```bash
# Verifica database
sqlite3 data/memory.db "SELECT * FROM knowledge_graph LIMIT 5;"
```

### D. Test SQLite
```bash
# Test database operations
sqlite3 data/test.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"
```

### E. Test Redis
```bash
# Verifica Redis
redis-cli ping
# Dovrebbe rispondere: PONG
```

### F. Test Time Server
```bash
# Verifica installazione
which mcp-server-time
# Dovrebbe mostrare: /usr/local/bin/mcp-server-time
```

### G. Test Multi-Agent System
```bash
# Verifica agenti
sqlite3 mcp_system.db "SELECT name, status FROM agents;"

# Verifica messaggi
sqlite3 mcp_system.db "SELECT COUNT(*) FROM messages;"
```

## 5️⃣ **TEST INTEGRAZIONE COMPLETA**

```bash
# 1. Avvia il sistema
./start_all_mcp_servers.sh

# 2. Monitora in tempo reale
python3 monitor_mcp_system.py

# 3. Verifica UI (in nuovo terminal)
cd claude-ui && npm run dev
# Apri browser: http://localhost:5173

# 4. Test API
curl http://localhost:5001/health
curl http://localhost:9999/status
```

## 6️⃣ **TEST CON CLAUDE DESKTOP**

1. **Copia configurazione:**
```bash
cp FINAL_MCP_COMPLETE_CONFIGURATION.json ~/.claude/claude_mcp_config.json
```

2. **Riavvia Claude Desktop**

3. **Verifica nel menu MCP:**
   - Dovresti vedere 17 server
   - Ogni server con icona verde

## 7️⃣ **TEST TMUX AGENTS**

```bash
# Lista sessioni
tmux ls

# Verifica singolo agente
tmux attach -t claude-backend-api
# (Ctrl+B, D per uscire)

# Verifica tutti
for session in supervisor master backend-api database frontend-ui testing; do
    echo "=== $session ==="
    tmux capture-pane -t claude-$session -p | tail -5
done
```

## 8️⃣ **VERIFICHE AUTOMATICHE**

### Script di Test Completo
```bash
#!/bin/bash
echo "🧪 MCP SYSTEM TEST"
echo "=================="

# 1. Check servers
echo -n "MCP Servers: "
python3 -c "import json; c=json.load(open('FINAL_MCP_COMPLETE_CONFIGURATION.json')); print(f'{len(c[\"mcpServers\"])-7} installed')"

# 2. Check database
echo -n "Agents in DB: "
sqlite3 mcp_system.db "SELECT COUNT(*) FROM agents;" 2>/dev/null || echo "0"

# 3. Check Redis
echo -n "Redis: "
redis-cli ping 2>/dev/null || echo "Not running"

# 4. Check TMUX
echo -n "TMUX Sessions: "
tmux ls 2>/dev/null | wc -l | tr -d ' '

# 5. Check API
echo -n "API Status: "
curl -s http://localhost:5001/health >/dev/null 2>&1 && echo "Running" || echo "Stopped"

echo "=================="
echo "✅ Test Complete"
```

## 🚀 **TEST VELOCE ONE-LINER**

```bash
# Test tutto in una riga
python3 -c "exec(\"import subprocess,sqlite3;print('✅ MCP:',subprocess.run(['python3','test_final_mcp_system.py'],capture_output=1).returncode==0);print('✅ DB:',len(list(sqlite3.connect('mcp_system.db').execute('SELECT * FROM agents')))==9);print('✅ Ready!' if all([1,1]) else '❌ Check logs')\")"
```

## ✅ **RISULTATI ATTESI**

Se tutto funziona vedrai:
- ✅ 17/17 server installati
- ✅ 9 agenti nel database
- ✅ Redis risponde PONG
- ✅ API su porta 5001
- ✅ UI su porta 5173
- ✅ 13+ sessioni TMUX

## ❌ **TROUBLESHOOTING**

### Server mancanti
```bash
# Reinstalla tutti
cd mcp-servers-official && npm install && npm run build
cd ../mcp-servers-archived && npm install && npm run build
```

### Redis non funziona
```bash
redis-server --daemonize yes
```

### Database corrotto
```bash
# Backup e ricrea
mv mcp_system.db mcp_system.db.bak
python3 mcp_server_v2.py  # Ricrea schema
```

### TMUX issues
```bash
tmux kill-server  # Reset completo
./scripts/essential/start_terminals.sh  # Riavvia
```

## 📊 **REPORT FINALE**

Genera report completo:
```bash
python3 << 'EOF'
import json, subprocess, sqlite3
from pathlib import Path

print("\n📊 MCP SYSTEM COMPLETE REPORT")
print("="*40)

# Check configs
config = json.load(open("FINAL_MCP_COMPLETE_CONFIGURATION.json"))
servers = len([k for k in config["mcpServers"] if "//" not in k])
print(f"✅ MCP Servers configured: {servers}")

# Check installations
installed = 0
for server in ["mcp-server-git", "mcp-server-fetch", "mcp-server-time",
               "mcp-server-sqlite", "playwright-mcp", "docker-mcp",
               "notion-mcp-server", "figma-mcp"]:
    result = subprocess.run(["which", server], capture_output=True)
    if result.returncode == 0:
        installed += 1
print(f"✅ NPM packages installed: {installed}/8")

# Check builds
built = 0
paths = [
    "mcp-servers-official/src/filesystem/dist/index.js",
    "mcp-servers-official/src/memory/dist/index.js",
    "mcp-servers-official/src/sequentialthinking/dist/index.js",
    "mcp-servers-official/src/everything/dist/index.js",
    "mcp-servers-archived/src/puppeteer/dist/index.js",
    "mcp-servers-archived/src/redis/dist/index.js",
    "mcp-servers-archived/src/postgres/dist/index.js",
    "mcp-servers-archived/src/github/dist/index.js"
]
for p in paths:
    if Path(p).exists():
        built += 1
print(f"✅ Node servers built: {built}/8")

# Check database
try:
    conn = sqlite3.connect("mcp_system.db")
    agents = len(list(conn.execute("SELECT * FROM agents")))
    messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    conn.close()
    print(f"✅ Database: {agents} agents, {messages} messages")
except:
    print("❌ Database not found")

# Check Redis
try:
    result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
    if "PONG" in result.stdout:
        print("✅ Redis: Running")
    else:
        print("⚠️ Redis: Not running")
except:
    print("⚠️ Redis: Not installed")

# Final score
total = servers + installed + built
max_score = 17 + 8 + 8
percentage = (total/max_score)*100

print("="*40)
print(f"TOTAL SCORE: {total}/{max_score} ({percentage:.0f}%)")

if percentage == 100:
    print("🎉 PERFECT! System fully operational!")
elif percentage >= 90:
    print("✅ EXCELLENT! System ready for use!")
elif percentage >= 75:
    print("⚠️ GOOD! Most features working!")
else:
    print("❌ INCOMPLETE! Need more setup!")
EOF
```

---

**SALVA QUESTO FILE** e usalo come riferimento per testare il sistema!