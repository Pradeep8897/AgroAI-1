const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';

async function main() {
  const opts = new chrome.Options().addArguments('--headless=new', '--no-sandbox', '--window-size=1440,1600');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();

  try {
    console.log('1. Clearing storage...');
    await driver.get(BASE);
    await driver.executeScript('localStorage.clear()');
    await new Promise(r => setTimeout(r, 1000));

    console.log('2. Navigating to login...');
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
    console.log('3. Logged in URL:', await driver.getCurrentUrl());

    // Visit /profile directly
    await driver.get(BASE + '/profile');
    await new Promise(r => setTimeout(r, 3000));
    console.log('4. Profile URL:', await driver.getCurrentUrl());

    let png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'farmer_profile_top.png'), Buffer.from(png, 'base64'));
    console.log('Saved: farmer_profile_top.png');

    await driver.executeScript('window.scrollTo(0, 500)');
    await new Promise(r => setTimeout(r, 1000));

    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'farmer_profile_bottom.png'), Buffer.from(png, 'base64'));
    console.log('Saved: farmer_profile_bottom.png');
  } finally {
    await driver.quit();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
