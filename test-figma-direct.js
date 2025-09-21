// Test connessione diretta a Figma
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3055');

ws.on('open', () => {
  console.log('Connected!');

  // Join al canale del plugin (sostituisci con il canale attuale)
  ws.send(JSON.stringify({
    type: 'join',
    channel: '5utu5pn0'  // Il canale che vedo nel plugin
  }));

  setTimeout(() => {
    // Crea un semplice testo
    const id = Date.now().toString();
    ws.send(JSON.stringify({
      id: id,
      type: 'message',
      channel: '5utu5pn0',
      message: {
        id: id,
        command: 'create_text',
        params: {
          x: 500,
          y: 100,
          text: '🤖 Ciao da Claude CLI direttamente!',
          fontSize: 32,
          fontWeight: 700,
          fontColor: {r: 0.2, g: 0.6, b: 1, a: 1},
          name: 'Direct Claude Message',
          commandId: id
        }
      }
    }));
    console.log('Sent create_text command!');
  }, 1000);

  setTimeout(() => {
    console.log('Done!');
    ws.close();
    process.exit(0);
  }, 2000);
});

ws.on('message', (data) => {
  console.log('Response:', JSON.parse(data.toString()).type || 'unknown');
});

ws.on('error', console.error);