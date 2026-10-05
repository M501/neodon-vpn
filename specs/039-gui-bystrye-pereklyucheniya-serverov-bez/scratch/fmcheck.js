const fs = require('fs'), path = require('path');
const KEYS = ['packet_pointer', 'last_updated_at', 'last_updated_by', 'recent_action', 'next_safe_action'];
for (const folder of process.argv.slice(2)) {
  console.log('==', folder);
  for (const doc of ['spec.md', 'plan.md', 'tasks.md', 'implementation-summary.md']) {
    const p = path.join(folder, doc);
    if (!fs.existsSync(p)) { console.log('  ', doc, 'MISSING'); continue; }
    const c = fs.readFileSync(p, 'utf8');
    const fm = c.match(/^---\n([\s\S]*?)\n---/u)?.[1];
    if (fm === undefined) { console.log('  ', doc, 'FRONTMATTER NOT MATCHED'); continue; }
    const miss = KEYS.filter(k => !new RegExp(`^\\s{4}${k}:`, 'mu').test(fm));
    console.log('  ', doc, miss.length ? ('MISSING ' + miss.join(',')) : 'ok');
  }
}
