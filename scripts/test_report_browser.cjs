const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PORT = 8089;
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
  const debuggingPort = 9333;
  
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

  // Wait for chrome debugging port
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
    console.log('Connected to target page:', pageTarget.url);

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

    // Wait 2s for page scripts to load and initialize
    await new Promise(r => setTimeout(r, 2000));

    // Verify report buttons exist
    const checkButtons = await send('Runtime.evaluate', {
      expression: `(() => {
        const headerBtn = document.getElementById('btn-header-report');
        const ctaBtn = document.querySelector('.report-cta-box .report-btn');
        const allReportButtons = [...document.querySelectorAll('button')].filter(b => b.textContent.includes('Vytvořit report'));
        return {
          hasHeaderBtn: Boolean(headerBtn),
          headerBtnText: headerBtn?.textContent?.trim(),
          hasCtaBtn: Boolean(ctaBtn),
          ctaBtnText: ctaBtn?.textContent?.trim(),
          reportButtonCount: allReportButtons.length
        };
      })()`,
      returnByValue: true
    });
    console.log('Buttons check:', checkButtons.result.value);

    // Open Report Modal
    const modalCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        openReportModal();
        const modal = document.getElementById('report-modal');
        const frame = document.getElementById('report-preview-frame');
        const printBtn = document.querySelector('.report-modal-actions .btn-print');
        const closeBtn = document.querySelector('.report-modal-actions button:last-child');
        
        let frameTitle = '';
        let frameHtml = '';
        if (frame && frame.contentDocument) {
          frameTitle = frame.contentDocument.title;
          frameHtml = frame.contentDocument.body.innerText;
          return {
            modalMounted: Boolean(modal),
            hasFrame: Boolean(frame),
            hasPrintBtn: Boolean(printBtn),
            hasCloseBtn: Boolean(closeBtn),
            frameTitle,
            fullText: frameHtml
          };
        }

        return {
          modalMounted: Boolean(modal),
          hasFrame: Boolean(frame),
          hasPrintBtn: Boolean(printBtn),
          hasCloseBtn: Boolean(closeBtn),
          frameTitle,
          hasHeroHp: frameHtml.includes('Tepelné čerpadlo'),
          hasHeroGas: frameHtml.includes('Plynový kotel'),
          hasHeroSaving: frameHtml.includes('Roční úspora s TČ'),
          hasHouseSection: frameHtml.includes('Dům, lokalita a spotřeba'),
          hasSimplifiedSection: frameHtml.includes('Zjednodušená konfigurace zdrojů tepla'),
          hasKeymarkBadge: frameHtml.includes('Keymark'),
          hasBoilerModel: frameHtml.includes('Protherm Gepard Condens') || frameHtml.includes('Plynový kotel'),
          hasEfficiency: frameHtml.includes('Hs') && frameHtml.includes('Hi'),
          has10SeasonsTable: frameHtml.includes('Víceletá bilance – srovnání 10 historických sezón'),
          hasAvgRow: frameHtml.includes('Průměr (10 sezón)')
        };
      })()`,
      returnByValue: true
    });
    console.log('Modal content check:', modalCheck.result.value);

    // Test printReport and downloadReportHtml without throwing
    const testFunctions = await send('Runtime.evaluate', {
      expression: `(() => {
        let printWorks = false;
        let downloadWorks = false;
        try {
          // printReport creates an iframe with id report-print-frame
          printReport();
          const pFrame = document.getElementById('report-print-frame');
          printWorks = Boolean(pFrame);
        } catch(e) {
          printWorks = false;
        }
        try {
          downloadReportHtml();
          downloadWorks = true;
        } catch(e) {
          downloadWorks = false;
        }
        closeReportModal();
        const closed = !document.getElementById('report-modal');
        return { printWorks, downloadWorks, closed };
      })()`,
      returnByValue: true
    });
    console.log('Function tests:', testFunctions.result.value);

    // Assertions
    const btn = checkButtons.result.value;
    const m = modalCheck.result.value;
    const fn = testFunctions.result.value;

    if (btn.reportButtonCount !== 1) {
      throw new Error(`Expected exactly 1 report button on page, found ${btn.reportButtonCount}`);
    }
    if (!btn.hasCtaBtn) {
      throw new Error('CTA report button not found in calculation panel');
    }
    if (btn.hasHeaderBtn) {
      throw new Error('Duplicate report button still present in header');
    }
    const textUpper = m.fullText.toUpperCase();
    if (!textUpper.includes('TEPELNÉ ČERPADLO') || !textUpper.includes('PLYNOVÝ KOTEL') || !textUpper.includes('ROČNÍ ÚSPORA')) {
      throw new Error('Hero summary missing from report');
    }
    if (!m.fullText.includes('Zjednodušená konfigurace') || !m.fullText.includes('Keymark')) {
      throw new Error('Simplified equipment configuration missing from report');
    }
    if (!m.fullText.includes('10 historických sezón') || !m.fullText.includes('Průměr (10 sezón)')) {
      throw new Error('Historical 10 season table missing from report');
    }
    if (!fn.closed) {
      throw new Error('Report modal failed to close');
    }

    console.log('ALL BROWSER REPORT TESTS PASSED PERFECTLY!');
    ws.close();
    cleanup();
    process.exit(0);
  } catch (err) {
    console.error('Test error:', err);
    cleanup();
    process.exit(1);
  }
});
