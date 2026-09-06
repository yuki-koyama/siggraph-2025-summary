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
  const html = pug.renderFile('src/templates/slides.pug', {
    ...paperData,
    pageTitle: eventConfig.pageTitle,
    sourceUrl: eventConfig.sourceUrl,
    sourceLabel: eventConfig.sourceLabel,
    deferredPolicyUrl: eventConfig.deferredPolicyUrl,
    pretty: true,
  });
  await fs.ensureDir(distDir);
  await fs.writeFile(path.join(distDir, 'slides.html'), html);
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
