# API Documentation

## Authentication Endpoints

### Login
**Endpoint:** `POST http://localhost:5002/api/auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "string",
  "role": "string",
  "expires_in": 86400
}
```

**Test Credentials:**
- Regular User: `user` / `user123`
- Admin: `admin` / `admin123`
- Backend API Agent: `backend-api` / `agent123`
- Frontend UI Agent: `frontend-ui` / `agent123`
- Supervisor: `supervisor` / `supervisor123`

### Token Verification
**Endpoint:** `GET http://localhost:5002/api/auth/verify`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "valid": true,
  "username": "string",
  "role": "string",
  "user_id": "string"
}
```

### Logout
**Endpoint:** `POST http://localhost:5002/api/auth/logout`

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Health Check

**Endpoint:** `GET http://localhost:5001/api/health`

**Response:**
```json
{
  "status": "ok"
}
```

## Usage Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:5002/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'user',
    password: 'user123'
  })
});

const { token } = await loginResponse.json();

// Use token for authenticated requests
const verifyResponse = await fetch('http://localhost:5002/api/auth/verify', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```