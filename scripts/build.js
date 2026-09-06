const fs = require('fs-extra');
const path = require('path');
const pug = require('pug');
const { EVENTS, getEventFromArgv } = require('./event-config');
const { preparePaperData } = require('./paper-data');

async function build() {
  const event = getEventFromArgv(process.argv);
  const eventConfig = EVENTS[event];
  const distDir = path.join('dist', event);
  const data = await fs.readJson(path.join(distDir, 'papers.json')).catch(() => []);
  const paperData = preparePaperData(data);
  // Render Pug template with pretty formatting so the resulting HTML is more readable
  const html = pug.renderFile('src/templates/index.pug', {
    ...paperData,
    pageTitle: eventConfig.pageTitle,
    sourceUrl: eventConfig.sourceUrl,
    sourceLabel: eventConfig.sourceLabel,
    deferredPolicyUrl: eventConfig.deferredPolicyUrl,
    pretty: true,
  });
  await fs.ensureDir(distDir);
  await fs.writeFile(path.join(distDir, 'index.html'), html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
