const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';

async function main() {
  const opts = new chrome.Options().addArguments('--headless=new', '--window-size=1440,900');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();

  try {
    await driver.get(BASE + '/login');
    await new Promise(r => setTimeout(r, 2000));

    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    await emailInput.clear();
    await emailInput.sendKeys('pradeepsangu950@gmail.com');

    const passInput = await driver.findElement(By.css('input[type="password"]'));
    await passInput.clear();
    await passInput.sendKeys('pradeep8897');

    const loginBtn = await driver.findElement(By.xpath("//button[contains(., 'Log in')]"));
    await driver.executeScript('arguments[0].click()', loginBtn);

    await new Promise(r => setTimeout(r, 3500));
    console.log('Current URL after login:', await driver.getCurrentUrl());

    const png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'user_login_success.png'), Buffer.from(png, 'base64'));
    console.log('Saved: user_login_success.png');
  } finally {
    await driver.quit();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
