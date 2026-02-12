const path = require('path');
const puppeteer = require('puppeteer');
const { getEventFromArgv } = require('./event-config');

async function build() {
  const event = getEventFromArgv(process.argv);
  const distDir = path.resolve(__dirname, '../dist', event);
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  const htmlPath = path.join(distDir, 'slides.html');
  await page.goto('file://' + htmlPath, {waitUntil: 'networkidle0'});
  await page.pdf({
    path: path.join(distDir, 'slides.pdf'),
    width: '1280px',
    height: '720px',
    printBackground: true,
    margin: {top: '0', right: '0', bottom: '0', left: '0'}
  });
  await browser.close();
}

build().catch(err => {
  console.error(err);
  process.exit(1);
});
