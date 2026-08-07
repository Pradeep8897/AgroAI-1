import { Builder, By } from 'selenium-webdriver';
import chrome from 'selenium-webdriver/chrome.js';
import fs from 'fs';
import path from 'path';

const FRONTEND_URL = 'http://localhost:5175';
const targetDir = 'C:\\Users\\prade\\.gemini\\antigravity-ide\\brain\\ea373096-abd3-4af3-81e6-41ccd0df6a29';

async function captureScreen(driver, filename) {
  const screenshot = await driver.takeScreenshot();
  const filePath = path.join(targetDir, filename);
  fs.writeFileSync(filePath, screenshot, 'base64');
  console.log(`Screenshot saved to ${filePath}`);
}

async function run() {
  const options = new chrome.Options();
  options.addArguments('--headless=new', '--disable-gpu', '--window-size=1280,800');
  const driver = await new Builder().forBrowser('chrome').setChromeOptions(options).build();

  try {
    // 1. Go to Login page (should not show authenticated links)
    console.log("Navigating to login page...");
    await driver.get(`${FRONTEND_URL}/login`);
    await driver.sleep(3000);
    
    // Check if dashboard link exists in DOM
    const navText = await driver.findElement(By.css('header')).getText();
    console.log("Header text on login page:", navText.replace(/\n/g, ' '));
    await captureScreen(driver, 'login_cleaned_navbar.png');

    // 2. Type credentials and submit
    console.log("Entering credentials to log in...");
    const emailInput = await driver.findElement(By.css('input[type="email"]'));
    const passwordInput = await driver.findElement(By.css('input[type="password"]'));
    
    await emailInput.sendKeys('pradeep@example.com');
    await passwordInput.sendKeys('password123');
    
    console.log("Clicking Sign In...");
    const submitBtn = await driver.findElement(By.css('form button'));
    await submitBtn.click();
    
    // Wait for redirect to dashboard
    await driver.sleep(5000);
    
    const currentUrl = await driver.getCurrentUrl();
    console.log("Current URL after login:", currentUrl);
    
    const loggedInNavText = await driver.findElement(By.css('header')).getText();
    console.log("Header text after login:", loggedInNavText.replace(/\n/g, ' '));
    await captureScreen(driver, 'dashboard_logged_in.png');

    // 3. Click Logout
    console.log("Clicking Logout button...");
    const logoutBtn = await driver.findElement(By.xpath("//button[contains(text(),'Logout')]"));
    await driver.executeScript("arguments[0].click();", logoutBtn);
    await driver.sleep(4000);

    const postLogoutUrl = await driver.getCurrentUrl();
    console.log("Current URL after logout click:", postLogoutUrl);

    const postLogoutNavText = await driver.findElement(By.css('header')).getText();
    console.log("Header text after logout:", postLogoutNavText.replace(/\n/g, ' '));
    await captureScreen(driver, 'after_logout.png');

    // Print browser logs
    console.log("\n--- Browser Console Logs ---");
    const logs = await driver.manage().logs().get('browser');
    for (const log of logs) {
      console.log(`[${log.level.name}] ${log.message}`);
    }
    console.log("----------------------------\n");

  } catch (err) {
    console.error("Error occurred during verification:", err);
  } finally {
    await driver.quit();
  }
}

run();
