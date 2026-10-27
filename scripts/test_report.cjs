const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

async function testReport() {
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const port = 9342;
  const chrome = spawn(chromePath, [
    '--headless=new',
    '--disable-gpu',
    '--window-size=1200,900',
    `--remote-debugging-port=${port}`,
    '--user-data-dir=' + require('os').tmpdir() + '/chrome-test-profile-' + Date.now(),
    'file:///d:/Ai/Vytapeni/review-update/index.html'
  ]);

  try {
    let version;
    for (let i = 0; i < 30; i++) {
      try {
        version = await new Promise((resolve, reject) => {
          http.get(`http://127.0.0.1:${port}/json/version`, res => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
          }).on('error', reject);
        });
        break;
      } catch (e) {
        await new Promise(r => setTimeout(r, 200));
      }
    }
    const list = await new Promise((resolve, reject) => {
      http.get(`http://127.0.0.1:${port}/json/list`, res => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => resolve(JSON.parse(data)));
      }).on('error', reject);
    });
    const page = list.find(t => t.type === 'page');
    const ws = new (globalThis.WebSocket || require('ws'))(page.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);

    let msgId = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const id = msgId++;
        const handler = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.id === id) {
            ws.removeEventListener('message', handler);
            if (msg.error) reject(msg.error);
            else resolve(msg.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id, method, params }));
      });
    }

    await new Promise(r => setTimeout(r, 1000));

    // Test buildReportData
    const res = await send('Runtime.evaluate', {
      expression: `(() => {
        if (typeof buildReportData === 'function') {
          return JSON.stringify(buildReportData());
        }
        return 'buildReportData not defined yet';
      })()`
    });
    console.log('buildReportData result:', res.result.value.slice(0, 100));

    ws.close();
  } finally {
    chrome.kill();
  }
}

testReport().catch(console.error);
