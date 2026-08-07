const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const opts = new chrome.Options().addArguments('--headless=new', '--no-sandbox', '--window-size=1440,900');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();

  try {
    await driver.get(BASE + '/login');
    await sleep(3500);
    console.log('Page loaded URL:', await driver.getCurrentUrl());
    const bodyText = await driver.findElement(By.tagName('body')).getText();
    console.log('Page Body Text:', bodyText.substring(0, 200));

    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    await emailInput.clear();
    await emailInput.sendKeys('pradeep@example.com');
    await sleep(500);

    const passInput = await driver.findElement(By.css('input[type="password"]'));
    await passInput.clear();
    await passInput.sendKeys('password123');
    await sleep(500);

    const buttons = await driver.findElements(By.css('button'));
    for (let b of buttons) {
      const text = await b.getText();
      if (text.includes('Log in')) {
        console.log('Clicking button:', text);
        await b.click();
        break;
      }
    }

    await sleep(4000);
    const logs = await driver.manage().logs().get('browser');
    console.log('BROWSER CONSOLE LOGS:');
    logs.forEach(l => console.log(l.level.name, l.message));
    console.log('Current URL after login submit:', await driver.getCurrentUrl());

    const tabs = ['Weather', 'Government Schemes', 'Nearby Services', 'Community', 'Settings'];
    for (const tab of tabs) {
      const btn = await driver.findElement(By.xpath(`//aside//button[contains(., '${tab}')]`));
      await driver.executeScript('arguments[0].click()', btn);
      await sleep(2000);
      const tabLogs = await driver.manage().logs().get('browser');
      console.log(`--- LOGS FOR TAB: ${tab} ---`);
      tabLogs.forEach(l => console.log(l.level.name, l.message));
      const h1List = await driver.findElements(By.tagName('h1'));
      for (let h of h1List) {
        console.log(`Tab '${tab}' H1:`, await h.getText());
      }
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
