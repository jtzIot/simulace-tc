const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 8092;
const server = http.createServer((req, res) => {
  let reqPath = req.url.split('?')[0];
  if (reqPath === '/') reqPath = '/index.html';
  const filePath = path.join(__dirname, '..', reqPath.replace(/^\//, ''));
  if (fs.existsSync(filePath)) {
    const ext = path.extname(filePath);
    const mime = ext === '.html' ? 'text/html; charset=utf-8' :
                 ext === '.js' ? 'text/javascript' :
                 ext === '.css' ? 'text/css' :
                 ext === '.json' ? 'application/json' : 'text/plain';
    res.writeHead(200, { 'Content-Type': mime });
    res.end(fs.readFileSync(filePath));
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(PORT, async () => {
  console.log(`Server running at http://localhost:${PORT}/index.html`);
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const debuggingPort = 9334;
  
  const chrome = spawn(chromePath, [
    '--headless=new',
    `--remote-debugging-port=${debuggingPort}`,
    '--disable-gpu',
    '--no-sandbox',
    '--disable-extensions',
    `http://localhost:${PORT}/index.html`
  ]);

  let killed = false;
  function cleanup() {
    if (killed) return;
    killed = true;
    try { chrome.kill(); } catch (e) {}
    try { server.close(); } catch (e) {}
  }

  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);

  async function waitForChrome() {
    for (let i = 0; i < 30; i++) {
      try {
        const res = await fetch(`http://127.0.0.1:${debuggingPort}/json`);
        const targets = await res.json();
        const page = targets.find(t => t.type === 'page');
        if (page && page.webSocketDebuggerUrl) return page;
      } catch (err) {}
      await new Promise(r => setTimeout(r, 200));
    }
    throw new Error('Chrome did not start or expose debugging endpoint in time');
  }

  try {
    const pageTarget = await waitForChrome();
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let id = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        const handler = (event) => {
          const raw = typeof event.data === 'string' ? event.data : event.data.toString();
          const parsed = JSON.parse(raw);
          if (parsed.id === msgId) {
            ws.removeEventListener('message', handler);
            if (parsed.error) reject(parsed.error);
            else resolve(parsed.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await send('Runtime.enable');
    await send('Page.enable');
    await new Promise(r => setTimeout(r, 2000));

    // Verify all Gree options exist in select
    const selectCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const select = document.getElementById('settings-hp-select');
        const options = Array.from(select.options).map(o => ({ value: o.value, text: o.text }));
        const greeOptions = options.filter(o => o.value.includes('gree'));
        return {
          totalOptions: options.length,
          greeOptions
        };
      })()`,
      returnByValue: true
    });
    console.log('Gree options in select:', selectCheck.result.value);

    // Switch to gree-versati-8 and recalculate
    const switchTest = await send('Runtime.evaluate', {
      expression: `(() => {
        selectKeymarkModel('gree-versati-8');
        const hp = state.activeHp;
        openReportModal();
        const frame = document.getElementById('report-preview-frame');
        const frameText = frame?.contentDocument?.body?.innerText || '';
        closeReportModal();
        return {
          activeId: hp.id,
          activeName: hp.name,
          certNo: hp.certNo,
          pDesign35: hp.pDesign35,
          scop35: hp.scop35,
          reportHasGree: frameText.includes('GRS-CQ8Pd/NpG4-E') || frameText.includes('041-K004-34')
        };
      })()`,
      returnByValue: true
    });
    console.log('Switch to Gree 8 kW test:', switchTest.result.value, switchTest.exceptionDetails?.exception?.description || '');

    // Switch to gree-versati-10 and recalculate
    const switchTest2 = await send('Runtime.evaluate', {
      expression: `(() => {
        selectKeymarkModel('gree-versati-10');
        const hp = state.activeHp;
        openReportModal();
        const frame = document.getElementById('report-preview-frame');
        const frameText = frame?.contentDocument?.body?.innerText || '';
        closeReportModal();
        return {
          activeId: hp.id,
          activeName: hp.name,
          certNo: hp.certNo,
          pDesign35: hp.pDesign35,
          scop35: hp.scop35,
          reportHasGree10: frameText.includes('GRS-CQ10PD/NPG4-E') && frameText.includes('041-K004-34')
        };
      })()`,
      returnByValue: true
    });
    console.log('Switch to Gree 10 kW test:', switchTest2.result.value, switchTest2.exceptionDetails?.exception?.description || '');

    const s1 = switchTest.result.value;
    const s2 = switchTest2.result.value;
    if (s1.activeId !== 'gree-versati-8' || s2.activeId !== 'gree-versati-10' || !s1.reportHasGree || !s2.reportHasGree10) {
      throw new Error('Gree heat pumps did not properly reflect in report');
    }

    console.log('ALL GREE TESTS PASSED IN BROWSER!');
    ws.close();
    cleanup();
    process.exit(0);
  } catch (e) {
    console.error('Browser test error:', e);
    cleanup();
    process.exit(1);
  }
});
