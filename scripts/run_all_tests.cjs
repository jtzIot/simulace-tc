const { execFileSync } = require('child_process');

const tests = [
  'scripts/test_catalog.cjs',
  'scripts/test_energy_prices.cjs',
  'scripts/test_audit.cjs',
  'scripts/test_household.cjs',
  'scripts/test_keymark.cjs',
  'scripts/test_report_browser.cjs',
  'scripts/test_gree_browser.cjs',
  'scripts/test_new_layout_absolute.cjs',
  'scripts/test_comfort_corridor.cjs'
];

for (const t of tests) {
  try {
    const out = execFileSync(process.execPath, [t], { encoding: 'utf8' });
    const lastLine = out.trim().split('\n').pop();
    console.log('✓', t, ':', lastLine);
  } catch (err) {
    console.error('✗', t, 'FAILED:', err.message);
    process.exit(1);
  }
}

console.log('\nALL 9 TEST SUITES PASSED CLEANLY!');
