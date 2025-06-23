const fs = require('fs-extra');
const pug = require('pug');

async function build() {
  const data = await fs.readJson('data/papers.json').catch(() => []);
  // Group papers by session title
  const sessionsMap = new Map();
  for (const paper of data) {
    const name = paper.session || 'Unknown Session';
    if (!sessionsMap.has(name)) {
      sessionsMap.set(name, []);
    }
    sessionsMap.get(name).push(paper);
  }
  const sessions = Array.from(sessionsMap, ([name, papers]) => ({ name, papers }));
  const html = pug.renderFile('src/templates/index.pug', { sessions });
  await fs.ensureDir('dist');
  await fs.writeFile('dist/index.html', html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
