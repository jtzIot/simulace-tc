const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const assert = require('node:assert/strict');

const PORT = 8094;
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
  const debuggingPort = 9338;
  
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
    throw new Error('Chrome did not start');
  }

  try {
    const pageTarget = await waitForChrome();
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
    await new Promise((resolve, resolveErr) => {
      ws.onopen = resolve;
      ws.onerror = resolveErr;
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
    await new Promise(r => setTimeout(r, 1500));

    // 1. Verify in Simple mode:
    const simpleCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const tolInput = document.getElementById('input-tolerance');
        const tinInput = document.getElementById('input-tin');
        const tolParent = tolInput?.closest('#slot-simple-comfort');
        const tolLabel = tolInput?.closest('.slider-input-row')?.previousElementSibling?.textContent;
        const corridor = document.getElementById('calc-room-corridor')?.textContent;
        return {
          hasTolInput: Boolean(tolInput),
          hasTinInput: Boolean(tinInput),
          inSimpleComfortSlot: Boolean(tolParent),
          tolLabel,
          corridor,
          currentTol: tolInput ? tolInput.value : null
        };
      })()`,
      returnByValue: true
    });

    console.log('Simple mode comfort check:', simpleCheck.result.value);
    const sc = simpleCheck.result.value;
    assert(sc.hasTolInput, 'Tolerance input exists in simple mode');
    assert(sc.inSimpleComfortSlot, 'Tolerance input is inside #slot-simple-comfort');
    assert(sc.tolLabel.includes('Hystereze směrem dolů') || sc.tolLabel.includes('pokles'), 'Tolerance label mentions hysteresis/drop');
    assert(sc.corridor.includes('nekomfort'), 'Corridor note mentions nekomfort');

    // 2. Switch to Advanced mode (Tab 2: Nastavení domu):
    await send('Runtime.evaluate', {
      expression: `selectConfigTab('house');`
    });
    await new Promise(r => setTimeout(r, 500));

    const advCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const tolInput = document.getElementById('input-tolerance');
        const tolInAdvSlot = tolInput?.closest('#slot-adv-comfort');
        const houseTab = tolInput?.closest('#content-house');
        const guidance = document.querySelector('.house-guidance')?.textContent;
        return {
          hasTolInput: Boolean(tolInput),
          inAdvComfortSlot: Boolean(tolInAdvSlot),
          inHouseTab: Boolean(houseTab),
          guidanceMentionsHysteresis: guidance?.includes('hysterezi')
        };
      })()`,
      returnByValue: true
    });

    console.log('Advanced mode (Tab 2: Nastavení domu) check:', advCheck.result.value);
    const ac = advCheck.result.value;
    assert(ac.hasTolInput, 'Tolerance input exists in advanced house tab');
    assert(ac.inAdvComfortSlot, 'Tolerance input is inside #slot-adv-comfort');
    assert(ac.inHouseTab, 'Tolerance input is located within #content-house');
    assert(ac.guidanceMentionsHysteresis, 'House guidance details mention hysteresis');

    // 3. Switch to Tab 6: Režimy řízení and verify #control-comfort summary
    await send('Runtime.evaluate', {
      expression: `selectConfigTab('control');`
    });
    await new Promise(r => setTimeout(r, 500));

    const ctrlCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const ctrlComfort = document.getElementById('control-comfort');
        return {
          text: ctrlComfort?.textContent,
          hasSummary: ctrlComfort?.textContent.includes('Komfort nastavený u domu'),
          hasButton: Boolean(ctrlComfort?.querySelector('button'))
        };
      })()`,
      returnByValue: true
    });

    console.log('Tab 6 control comfort summary check:', ctrlCheck.result.value);
    const cc = ctrlCheck.result.value;
    assert(cc.hasSummary, 'Tab 6 displays house comfort summary');
    assert(cc.hasButton, 'Tab 6 summary has link/button back to house tab');

    console.log('ALL COMFORT CORRIDOR / HYSTERESIS TESTS PASSED PERFECTLY!');
    cleanup();
    process.exit(0);
  } catch (err) {
    console.error('TEST FAILED:', err);
    cleanup();
    process.exit(1);
  }
});
