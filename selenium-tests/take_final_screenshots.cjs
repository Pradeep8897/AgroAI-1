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
    console.log('Logging in...');
    await driver.get(BASE + '/login');
    await sleep(2500);

    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    await emailInput.clear();
    await emailInput.sendKeys('pradeep@example.com');

    const passInput = await driver.findElement(By.css('input[type="password"]'));
    await passInput.clear();
    await passInput.sendKeys('password123');

    const loginBtn = await driver.findElement(By.xpath("//button[contains(., 'Log in')]"));
    await driver.executeScript('arguments[0].click()', loginBtn);
    await sleep(3500);

    console.log('Logged in URL:', await driver.getCurrentUrl());

    // 1. Marketplace with images
    await driver.get(BASE + '/marketplace');
    await sleep(3000);
    let png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'marketplace_with_images.png'), Buffer.from(png, 'base64'));
    console.log('Saved: marketplace_with_images.png');

    // 2. AI Disease Detection Working
    await driver.get(BASE + '/ai-disease-detection');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'ai_disease_detection_working.png'), Buffer.from(png, 'base64'));
    console.log('Saved: ai_disease_detection_working.png');

    // 3. Admin Panel Working
    await driver.get(BASE + '/admin');
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'admin_panel_working.png'), Buffer.from(png, 'base64'));
    console.log('Saved: admin_panel_working.png');

    // 4. Nearby Services with Google Maps
    await driver.get(BASE + '/dashboard');
    await sleep(2500);
    const servicesBtn = await driver.findElement(By.xpath("//aside//button[contains(., 'Nearby Services')]"));
    await driver.executeScript('arguments[0].click()', servicesBtn);
    await sleep(3000);
    png = await driver.takeScreenshot();
    fs.writeFileSync(path.join(OUT, 'nearby_services_google_maps.png'), Buffer.from(png, 'base64'));
    console.log('Saved: nearby_services_google_maps.png');

    console.log('ALL FINAL SCREENSHOTS CAPTURED SUCCESSFULLY!');
  } finally {
    await driver.quit();
  }
}

main().catch(e => { console.error(e.message); process.exit(1); });
