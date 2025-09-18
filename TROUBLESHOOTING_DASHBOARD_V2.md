# 🔧 Troubleshooting Guide - Dashboard V2

## ⚡ Quick Fix for Common Issues

### 🔴 Problem: Infinite Loading / Timeout Errors

**Symptoms:**
```
- Loading spinner never stops
- Console error: "timeout of 5000ms exceeded"
- Console error: "Network Error" or "ECONNABORTED"
```

**Solution:**

1. **Check API is running:**
```bash
# Check if API is on port 8888
lsof -i :8888

# If not running, start it:
cd api
uvicorn main:socket_app --host 0.0.0.0 --port 8888 --reload
```

2. **Check Redis is running:**
```bash
# Check Redis
redis-cli ping

# If not running:
redis-server
```

3. **Use the correct configuration (ALREADY FIXED):**
- ✅ Vite proxy configured in `vite.config.ts`
- ✅ API calls use relative paths (`/api/...`)
- ✅ CORS handled by proxy
- ✅ Timeouts set to 15 seconds

### 🟡 Problem: CORS Errors

**Symptoms:**
```
Access to XMLHttpRequest at 'http://localhost:8888/api/agents'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
The Vite proxy is already configured to handle this. Make sure:
1. You're accessing the dashboard at `http://localhost:5173` (NOT opening the HTML file directly)
2. The `vite.config.ts` has the proxy configuration (already done)
3. API calls use relative paths without the full URL

### 🟢 Problem: Data Not Updating

**Symptoms:**
- Agent status doesn't change
- Metrics show old data
- No real-time updates

**Solution:**
1. The dashboard polls every 30 seconds (not real-time WebSocket yet)
2. To force refresh: Reload the page (Cmd+R / F5)
3. Check browser console for API errors

## 📋 Setup Checklist

```bash
# 1. Start Redis
redis-server

# 2. Start Backend API (in api/ folder)
uvicorn main:socket_app --host 0.0.0.0 --port 8888 --reload

# 3. Start Frontend (in claude-ui/ folder)
npm install  # First time only
npm run dev

# 4. Open Browser
open http://localhost:5173
```

## 🔍 Debug Commands

### Check what's running:
```bash
# Check ports
lsof -i :5173  # Frontend
lsof -i :8888  # API
lsof -i :6379  # Redis

# Test API directly
curl http://localhost:8888/api/agents
curl http://localhost:8888/api/system/health
```

### Check logs:
```bash
# See API logs
# Look at the terminal where you started uvicorn

# See frontend logs
# Open browser console (F12)
```

## 🛠️ Configuration Files

### 1. `claude-ui/vite.config.ts`
```typescript
// MUST HAVE this proxy configuration:
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8888',
      changeOrigin: true,
      secure: false,
    },
  },
}
```

### 2. `claude-ui/src/context/AppContext.tsx`
```typescript
// DO NOT set baseURL:
// ❌ axios.defaults.baseURL = config.API_URL;

// Use relative paths:
// ✅ await axios.get('/api/agents');
```

### 3. `api/main.py`
```python
# CORS should allow all origins for development:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 💡 Pro Tips

1. **Always use the Vite dev server** - Never open HTML files directly
2. **Check the browser console** - Most errors are logged there
3. **API calls should be relative** - Use `/api/...` not `http://localhost:8888/api/...`
4. **The proxy handles CORS** - Don't try to fix CORS in the browser
5. **Polling is every 30 seconds** - Be patient or refresh manually

## 🚨 Emergency Reset

If nothing works:

```bash
# 1. Kill everything
pkill -f uvicorn
pkill -f vite
pkill -f node

# 2. Clear cache
rm -rf claude-ui/node_modules/.vite

# 3. Restart everything
cd api && uvicorn main:socket_app --host 0.0.0.0 --port 8888 --reload &
cd ../claude-ui && npm run dev &

# 4. Open fresh browser window
open -n -a "Google Chrome" --args --incognito http://localhost:5173
```

## 📞 Still Having Issues?

1. Check this guide first
2. Look at browser console for errors
3. Check API is responding: `curl http://localhost:8888/api/agents`
4. Verify Redis is running: `redis-cli ping`
5. Make sure you're using the Vite dev server, not opening files directly

---

**Last Updated**: September 18, 2025
**Version**: Dashboard V2 (React + Vite)
**Status**: 65% Complete - Development Version