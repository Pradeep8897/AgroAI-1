const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const http = require('http');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';
const sleep = ms => new Promise(r => setTimeout(r, ms));

function getToken() {
  return new Promise((res, rej) => {
    const body = JSON.stringify({ email: 'pradeep@example.com', password: 'password123' });
    const req = http.request(
      { host: 'localhost', port: 5000, path: '/api/auth/login', method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': body.length } },
      (r) => { let d = ''; r.on('data', c => d += c); r.on('end', () => res(JSON.parse(d).access_token)); }
    );
    req.on('error', rej); req.write(body); req.end();
  });
}

async function main() {
  const opts = new chrome.Options().addArguments('--headless=new', '--no-sandbox', '--window-size=1440,900');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();
  try {
    const token = await getToken();
    console.log('Got API Token:', token.substring(0, 25) + '...');

    await driver.get(BASE + '/login');
    await sleep(1000);
    await driver.executeScript(function(t) {
      window.localStorage.setItem('agroai_token', t);
    }, token);
    await sleep(500);

    const checkToken = await driver.executeScript(function() {
      return window.localStorage.getItem('agroai_token');
    });
    console.log('Verified token in localStorage:', checkToken ? checkToken.substring(0, 25) + '...' : 'NULL');

    await driver.get(BASE + '/dashboard');
    await sleep(3500);

    console.log('Current Dashboard URL:', await driver.getCurrentUrl());

    const tabs = ['Weather', 'Government Schemes', 'Nearby Services', 'Community', 'Settings'];
    for (const tab of tabs) {
      const btn = await driver.findElement(By.xpath(`//button[contains(., '${tab}')]`));
      await btn.click();
      await sleep(1500);
      const png = await driver.takeScreenshot();
      const fname = 'sidebar_' + tab.toLowerCase().replace(/\s+/g, '_') + '.png';
      fs.writeFileSync(path.join(OUT, fname), Buffer.from(png, 'base64'));
      console.log('Verified & Saved: ' + fname);
    }
    console.log('ALL SIDEBAR TABS VERIFIED SUCCESSFULLY!');
  } finally {
    await driver.quit();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
