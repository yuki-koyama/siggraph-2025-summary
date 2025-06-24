const fs = require('fs-extra');
const pug = require('pug');

async function build() {
  const data = await fs.readJson('dist/papers.json').catch(() => []);
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
  // Render Pug template with pretty formatting so the resulting HTML is more readable
  const html = pug.renderFile('src/templates/index.pug', {
    sessions,
    pretty: true,
  });
  await fs.ensureDir('dist');
  await fs.writeFile('dist/index.html', html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
