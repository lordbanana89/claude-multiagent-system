// Quick fix to join the right channel
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3055');

ws.on('open', () => {
  console.log('Connected to WebSocket server');

  // Join the Figma plugin channel
  const joinMessage = {
    type: 'join',
    channel: 'n0tc0hk0' // Il canale del plugin Figma
  };

  ws.send(JSON.stringify(joinMessage));
  console.log('Joined channel n0tc0hk0');

  // Now relay messages between channels
  console.log('Bridge active between channels...');
});

ws.on('message', (data) => {
  console.log('Message:', data.toString());
});

console.log('Channel bridge starting...');