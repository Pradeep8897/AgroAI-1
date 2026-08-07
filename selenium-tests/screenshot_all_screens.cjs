const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const http = require('http');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';

function getToken() {
  return new Promise((res, rej) => {
    const body = JSON.stringify({ email: 'pradeep@example.com', password: 'password123' });
    const req = http.request(
      { host: 'localhost', port: 5000, path: '/api/auth/login', method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': body.length } },
      (r) => { let d = ''; r.on('data', c => d += c); r.on('end', () => res(JSON.parse(d).access_token)); }
    );
    req.on('error', rej);
    req.write(body);
    req.end();
  });
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const opts = new chrome.Options()
    .addArguments('--headless=new', '--no-sandbox', '--window-size=1440,900', '--disable-gpu');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();

  try {
    const token = await getToken();
    console.log('Got token:', token.substring(0, 30) + '...');

    // Plant token into localStorage
    await driver.get(BASE + '/login');
    await sleep(1500);
    await driver.executeScript(`localStorage.setItem('agroai_token', '${token}')`);

    const pages = [
      ['dashboard_with_data',   '/dashboard'],
      ['marketplace_with_data', '/marketplace'],
      ['ai_detect_with_data',   '/ai-disease-detection'],
      ['admin_with_data',       '/admin'],
    ];

    for (const [name, url] of pages) {
      await driver.get(BASE + url);
      await sleep(3500);
      const logs = await driver.manage().logs().get('browser');
      console.log(`--- LOGS FOR ${name} ---`);
      logs.forEach(l => console.log(l.level.name, l.message));
      const png = await driver.takeScreenshot();
      fs.writeFileSync(path.join(OUT, name + '.png'), Buffer.from(png, 'base64'));
      console.log('Saved: ' + name + '.png');
    }

    console.log('All screenshots done!');
  } finally {
    await driver.quit();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
