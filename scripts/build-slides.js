const fs = require('fs-extra');
const pug = require('pug');

async function build() {
  const data = await fs.readJson('dist/papers.json').catch(() => []);
  const sessionsMap = new Map();
  for (const paper of data) {
    const name = paper.session || 'Unknown Session';
    if (!sessionsMap.has(name)) {
      sessionsMap.set(name, []);
    }
    sessionsMap.get(name).push(paper);
  }
  const sessions = Array.from(sessionsMap, ([name, papers]) => ({ name, papers }));
  const sessionCount = sessions.length;
  const paperCount = data.length;
  const html = pug.renderFile('src/templates/slides.pug', {
    sessions,
    sessionCount,
    paperCount,
    pretty: true,
  });
  await fs.ensureDir('dist');
  await fs.writeFile('dist/slides.html', html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
