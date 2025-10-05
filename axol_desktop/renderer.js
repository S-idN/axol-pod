const { ipcRenderer } = require('electron');
const path = require('path');

const chat = document.getElementById('chat');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const uploadBtn = document.getElementById('upload-btn');
const axolSprite = document.getElementById('axol-sprite');

// Functions to animate axolotl
function setAxolIdle() {
  axolSprite.classList.remove('talking-mouth');
}

function setAxolTalking() {
  axolSprite.classList.add('talking-mouth');
}

// Handle sending message
sendBtn.addEventListener('click', async () => {
  const msg = input.value.trim();
  if (!msg) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = 'message';
  msgDiv.innerHTML = `<strong>You:</strong> ${msg}`;
  chat.appendChild(msgDiv);
  chat.scrollTop = chat.scrollHeight;
  input.value = '';

  setAxolIdle(); // Thinking...
  await ipcRenderer.invoke('user-input', msg);
});

// Enter key
input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendBtn.click();
});

// Python responses
ipcRenderer.on('python-response', (event, response) => {
  setAxolTalking(); // AI responding

  const botDiv = document.createElement('div');
  botDiv.className = 'message';
  botDiv.innerHTML = `<strong>Axol:</strong> ${response}`;
  chat.appendChild(botDiv);
  chat.scrollTop = chat.scrollHeight;

  setTimeout(setAxolIdle, 500); // back to idle after response
});

// File upload
uploadBtn.addEventListener('click', async () => {
  const files = await ipcRenderer.invoke('upload-file');
  if (files.length > 0) {
    const fileMsg = document.createElement('div');
    fileMsg.className = 'message';
    fileMsg.innerHTML = `<strong>System:</strong> Uploaded: ${files.map(f => path.basename(f)).join(', ')}`;
    chat.appendChild(fileMsg);
    chat.scrollTop = chat.scrollHeight;
  }
});
