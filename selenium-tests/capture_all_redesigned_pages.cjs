const { Builder, By } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const fs = require('fs');
const path = require('path');

const OUT = 'C:/Users/prade/.gemini/antigravity-ide/brain/ea373096-abd3-4af3-81e6-41ccd0df6a29';
const BASE = 'http://localhost:5173';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const opts = new chrome.Options().addArguments('--headless=new', '--no-sandbox', '--window-size=1440,1600');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(opts).build();

  try {
    console.log('1. Capturing Redesigned Login Landing Page...');
    await driver.get(BASE + '/login');
    await driver.executeScript('localStorage.clear()');
    await driver.get(BASE + '/login');
    await sleep(2000);

    let png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_login_screen.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_login_screen.png');

    // 2. Capturing Redesigned Register Wizard
    console.log('2. Capturing Register Wizard...');
    await driver.get(BASE + '/register');
    await sleep(2000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_register_wizard.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_register_wizard.png');

    // Perform Login
    console.log('3. Logging in with pradeepsangu950@gmail.com...');
    await driver.get(BASE + '/login');
    await sleep(2000);

    const emailInput = await driver.findElement(By.css('input[name="identifier"]'));
    await emailInput.clear();
    await emailInput.sendKeys('pradeepsangu950@gmail.com');

    const passInput = await driver.findElement(By.css('input[type="password"]'));
    await passInput.clear();
    await passInput.sendKeys('pradeep8897');

    const loginBtn = await driver.findElement(By.xpath("//button[contains(., 'Log In')]"));
    await driver.executeScript('arguments[0].click()', loginBtn);
    await sleep(3000);

    // 4. Capturing Dashboard
    console.log('4. Capturing Redesigned Dashboard...');
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_dashboard.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_dashboard.png');

    // 5. Capturing Marketplace
    console.log('5. Capturing Redesigned Marketplace...');
    await driver.get(BASE + '/marketplace');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_marketplace.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_marketplace.png');

    // 6. Capturing Profile Page
    console.log('6. Capturing Redesigned Profile Page...');
    await driver.get(BASE + '/profile');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_profile_page.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_profile_page.png');

    // 7. Capturing AI Disease Detection
    console.log('7. Capturing Redesigned AI Disease Detection...');
    await driver.get(BASE + '/ai-disease-detection');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_ai_disease.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_ai_disease.png');

    // 8. Capturing Admin Panel
    console.log('8. Capturing Admin Panel...');
    await driver.get(BASE + '/admin');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'redesign_admin_panel.png'), Buffer.from(png, 'base64'));
    console.log('Saved: redesign_admin_panel.png');

    console.log('ALL REDESIGNED PAGE SCREENSHOTS CAPTURED SUCCESSFULLY!');
  } finally {
    await driver.quit();
  }
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
