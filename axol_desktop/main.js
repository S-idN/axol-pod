const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let pyProc;
let win;

function createWindow() {
  win = new BrowserWindow({
    autoHideMenuBar:true,
    width: 800,
    height: 600,
    minWidth: 600,
    minHeight: 400,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  win.loadFile('index.html');

  // Spawn Python process
  const script = path.join(__dirname, '../main.py');
  pyProc = spawn('python', [script]);

  pyProc.stdout.on('data', (data) => {
    const message = data.toString().trim();
    if (message && win) {
      win.webContents.send('python-response', message);
    }
  });

  pyProc.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  pyProc.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pyProc) pyProc.kill();
  if (process.platform !== 'darwin') app.quit();
});

// Handle user input from renderer
ipcMain.handle('user-input', (event, userInput) => {
  if (pyProc) {
    pyProc.stdin.write(userInput + '\n');
  }
});

// Handle file uploads (keep your existing knowledgeBase logic)
ipcMain.handle('upload-file', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections'],
  });

  if (canceled) return [];

  const savedFiles = [];
  const knowledgeBaseDir = path.join(__dirname, '../knowledgeBase');

  if (!fs.existsSync(knowledgeBaseDir)) fs.mkdirSync(knowledgeBaseDir, { recursive: true });

  filePaths.forEach(file => {
    const fileName = path.basename(file);
    const dest = path.join(knowledgeBaseDir, fileName);
    fs.copyFileSync(file, dest);
    savedFiles.push(dest);
  });

  return savedFiles;
});
