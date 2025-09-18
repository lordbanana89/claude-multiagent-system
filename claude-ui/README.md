# Claude Multi-Agent System - React Dashboard V2

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start the development server
npm run dev

# The dashboard will be available at http://localhost:5173
```

## ⚠️ IMPORTANT: API Connection Setup

### The dashboard uses a Vite proxy to connect to the backend API. This avoids CORS issues.

**Configuration is already done in `vite.config.ts`:**
- All requests to `/api/*` are proxied to `http://localhost:8888`
- WebSocket connections to `/ws/*` are proxied to `ws://localhost:8888`

### Prerequisites

1. **Backend API must be running on port 8888**:
   ```bash
   cd ../api
   uvicorn main:socket_app --host 0.0.0.0 --port 8888 --reload
   ```

2. **Redis must be running** (for message queue):
   ```bash
   redis-server
   ```

## 🔧 Configuration

### API Configuration (`src/config.ts`)
- `API_URL`: Backend API URL (default: `http://localhost:8888`)
- `WS_URL`: WebSocket URL (default: `ws://localhost:8888`)
- `POLL_INTERVAL`: How often to refresh data (default: 30000ms)

### Vite Proxy Configuration (`vite.config.ts`)
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8888',
      changeOrigin: true,
      secure: false,
    },
    '/ws': {
      target: 'ws://localhost:8888',
      ws: true,
      changeOrigin: true,
    },
  },
}
```

## 🐛 Common Issues & Solutions

### Issue 1: Infinite Loading / Timeout Errors

**Symptoms:**
- Dashboard shows infinite loading spinner
- Console shows "timeout of XXXXms exceeded"
- API calls fail with ECONNABORTED

**Solution:**
1. Ensure the backend API is running on port 8888
2. Check that Vite proxy is configured (already done)
3. Do NOT set `axios.defaults.baseURL` in AppContext
4. Use relative paths for API calls (e.g., `/api/agents` not `http://localhost:8888/api/agents`)

### Issue 2: CORS Errors

**Symptoms:**
- Browser console shows CORS policy errors
- OPTIONS requests fail with 405

**Solution:**
- Use the Vite proxy (already configured)
- Never call the API directly from the browser
- All API calls should go through the proxy

### Issue 3: "Could not Fast Refresh" Warning

**Symptoms:**
- Console warning about Fast Refresh
- Page reloads instead of hot module replacement

**Solution:**
- This is normal for Context providers
- Does not affect functionality
- Can be ignored

## 📁 Project Structure

```
claude-ui/
├── src/
│   ├── components/       # React components
│   ├── context/          # AppContext for state management
│   ├── config.ts         # Configuration file
│   └── main.tsx          # Entry point
├── vite.config.ts        # Vite configuration with proxy
└── package.json          # Dependencies
```

## 🔍 Development Tips

### Debugging API Calls
The AppContext includes axios interceptors that log all requests/responses to the console:
- Request details: URL, method, headers
- Response details: Status, data
- Errors: Detailed error messages

### Timeouts
All API calls have a 15-second timeout. If your backend is slow:
1. Check backend performance
2. Increase timeouts in `AppContext.tsx`
3. Consider implementing loading states

### Polling
The dashboard polls for updates every 30 seconds. To change:
- Edit `pollInterval` in `AppContext.tsx` (line ~493)

## 🚀 Production Deployment

For production:
1. Build the frontend:
   ```bash
   npm run build
   ```

2. Update `vite.config.ts` for production proxy or use nginx

3. Set environment variables:
   ```bash
   VITE_API_URL=https://your-api-domain.com
   ```

## 📊 Dashboard Features

- **Real-time Agent Monitoring**: See status of all 9 agents
- **System Health**: Monitor Redis, Queue, and component health
- **Workflow Builder**: Visual workflow creation (in development)
- **Operations View**: Manage agent tasks and queues
- **Monitoring View**: System metrics and logs
- **Dark Theme**: Built-in dark mode support

## 🛠️ Technologies

- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Axios** for HTTP requests
- **React Flow** for workflow visualization
- **Recharts** for data visualization

## 📝 Notes

- The dashboard is currently at 65% completion
- WebSocket real-time updates are planned but not yet implemented
- Authentication is not yet implemented
- Some data is still mocked (will be replaced with real data)

---

Last Updated: September 18, 2025
Version: 2.0.0-beta