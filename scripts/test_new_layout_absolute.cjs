const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const assert = require('node:assert/strict');

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
  const debuggingPort = 9335;
  
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
    await new Promise(r => setTimeout(r, 2000));

    // Test DOM layout requirements
    const layoutCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const gasTab = document.getElementById('content-gas');
        const tariffsTab = document.getElementById('content-tariffs');
        
        // 1. Reference tariff field in Gas Tab
        const refField = document.getElementById('energy-reference-field');
        const refParent = refField ? refField.closest('#content-gas') : null;
        
        // 2. GasNet section in Tariffs Tab
        const gasSection = document.querySelector('#energy-form .energy-grid > section:nth-child(2)');
        const gasSectionHeading = gasSection?.querySelector('h3')?.textContent?.trim();
        const gasSectionInTariffs = gasSection ? Boolean(gasSection.closest('#content-tariffs')) : false;
        const gasSectionInGasTab = gasSection ? Boolean(gasSection.closest('#content-gas')) : false;

        // 3. Absence of scope switch
        const scopeSwitch = document.querySelector('.scope-switch');
        const reportButtonsCount = [...document.querySelectorAll('button')].filter(b => b.textContent.includes('Vytvořit report')).length;
        
        // 4. Hero cost boxes and calculation
        const hpBoxText = document.querySelector('.hero-cost-box.hp')?.innerText;
        const gasBoxText = document.querySelector('.hero-cost-box.gas')?.innerText;
        const savingText = document.querySelector('.result-saving')?.innerText;
        const wholeHouseHeading = document.querySelector('.whole-house-heading')?.innerText;

        // 5. Calculation detail table rows
        const tableRows = [...document.querySelectorAll('.calculation-table tbody tr')].map(r => ({
          label: r.querySelector('th')?.textContent?.trim(),
          tc: r.querySelectorAll('td')[0]?.textContent?.trim(),
          gas: r.querySelectorAll('td')[1]?.textContent?.trim()
        }));

        return {
          refInGasTab: Boolean(refParent),
          gasSectionInTariffs,
          gasSectionInGasTab,
          gasSectionHeading,
          hasScopeSwitch: Boolean(scopeSwitch),
          reportButtonsCount,
          wholeHouseHeading,
          hpBoxText,
          gasBoxText,
          savingText,
          tableRows
        };
      })()`,
      returnByValue: true
    });

    console.log('Layout check:', layoutCheck.result.value);
    const v = layoutCheck.result.value;

    assert(v.refInGasTab, 'Reference tariff field must be in Tab 4 (Plynový kotel)');
    assert(v.gasSectionInTariffs, 'GasNet ceník section must be in Tab 5 (Tarify)');
    assert(!v.gasSectionInGasTab, 'GasNet ceník section must NOT be in Tab 4');
    assert.equal(v.gasSectionHeading, '🔥 Ceník plynu (GasNet) a scénář ETS 2');
    assert(!v.hasScopeSwitch, 'Scope switch (toggle) must be removed from calculation');
    assert.equal(v.reportButtonsCount, 1, 'There must be exactly 1 report button on the page');
    assert(v.wholeHouseHeading.includes('PROVOZ CELÉHO DOMU'), 'Heading must reflect whole-house operation');

    // Check that table has items for electric breaker for both TČ and Gas
    const breakerRow = v.tableRows.find(r => r.label.includes('jistič'));
    assert(breakerRow, 'Table must contain breaker row');
    console.log('Breaker row:', breakerRow);
    assert.notEqual(breakerRow.gas, '0', 'Gas must have non-zero electrical breaker fee');
    assert.notEqual(breakerRow.tc, '0', 'TČ must have non-zero electrical breaker fee');

    // Verify changing reference tariff
    const changeTariffCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const sel = document.getElementById('energy-referenceTariff');
        const beforeGasCost = document.querySelector('.hero-cost-box.gas strong')?.innerText;
        sel.value = 'D01d';
        sel.dispatchEvent(new Event('change'));
        const afterGasCost = document.querySelector('.hero-cost-box.gas strong')?.innerText;
        const refNote = document.getElementById('gas-reference-tariff-note')?.innerText;
        return { beforeGasCost, afterGasCost, refNote };
      })()`,
      returnByValue: true
    });
    console.log('Reference tariff switch to D01d:', changeTariffCheck.result.value);
    assert(changeTariffCheck.result.value.refNote.includes('D01d'), 'Breaker note must update to D01d');

    // Verify economyPeriod dropdown options (no "Topná sezóna", only "Modelový rok" and "Průměr desetiletí")
    const economyPeriodCheck = await send('Runtime.evaluate', {
      expression: `(() => {
        const sel = document.querySelector('.result-header select');
        const options = [...sel.options].map(o => ({ value: o.value, text: o.text.trim() }));
        const hasTopnaSezona = options.some(o => o.text.includes('Topná sezóna'));
        const hasPrumerDesetileti = options.some(o => o.text.includes('Průměr desetiletí'));
        const hasModelovyRok = options.some(o => o.text.includes('Modelový rok'));

        // Test switching to decade
        sel.value = 'decade';
        sel.dispatchEvent(new Event('change'));
        const decadeSubtitle = document.querySelector('.result-subtitle')?.innerText;
        const decadeSaving = document.querySelector('.result-saving')?.innerText;

        // Test switching to annual
        sel.value = 'annual';
        sel.dispatchEvent(new Event('change'));
        const annualSubtitle = document.querySelector('.result-subtitle')?.innerText;
        const annualSaving = document.querySelector('.result-saving')?.innerText;

        return {
          options,
          hasTopnaSezona,
          hasPrumerDesetileti,
          hasModelovyRok,
          decadeSubtitle,
          decadeSaving,
          annualSubtitle,
          annualSaving
        };
      })()`,
      returnByValue: true
    });
    console.log('Economy period dropdown check:', economyPeriodCheck.result.value);
    const ep = economyPeriodCheck.result.value;
    assert(!ep.hasTopnaSezona, 'Option "Topná sezóna" must be removed from dropdown');
    assert(ep.hasPrumerDesetileti, 'Option "Průměr desetiletí" must be present');
    assert(ep.hasModelovyRok, 'Option "Modelový rok" must be present');
    assert(ep.decadeSubtitle.includes('10 sezón'), 'Decade mode must show 10 seasons average');
    assert(ep.annualSubtitle.includes('Modelový rok'), 'Annual mode must show Modelový rok');

    console.log('ALL VERIFICATIONS PASSED SUCCESSFULLY!');
    cleanup();
    process.exit(0);
  } catch (err) {
    console.error('Test error:', err);
    cleanup();
    process.exit(1);
  }
});
