const path = require('path');
const puppeteer = require('puppeteer');

async function build() {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  const htmlPath = path.resolve(__dirname, '../dist/slides.html');
  await page.goto('file://' + htmlPath, {waitUntil: 'networkidle0'});
  await page.pdf({
    path: path.resolve(__dirname, '../dist/slides.pdf'),
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
