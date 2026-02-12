const fs = require('fs-extra');
const path = require('path');
const pug = require('pug');
const { EVENTS, getEventFromArgv } = require('./event-config');

async function build() {
  const event = getEventFromArgv(process.argv);
  const eventConfig = EVENTS[event];
  const distDir = path.join('dist', event);
  const data = await fs.readJson(path.join(distDir, 'papers.json')).catch(() => []);
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
    pageTitle: eventConfig.pageTitle,
    sourceUrl: eventConfig.sourceUrl,
    sourceLabel: eventConfig.sourceLabel,
    pretty: true,
  });
  await fs.ensureDir(distDir);
  await fs.writeFile(path.join(distDir, 'index.html'), html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
