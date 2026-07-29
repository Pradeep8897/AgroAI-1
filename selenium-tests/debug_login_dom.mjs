import { Builder, By, until } from 'selenium-webdriver';
import chrome from 'selenium-webdriver/chrome.js';

(async () => {
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(new chrome.Options().addArguments('--headless=new', '--disable-gpu', '--window-size=1280,1024'))
    .build();
  try {
    await driver.get('http://127.0.0.1:5173/login');
    await driver.wait(until.elementLocated(By.id('login-email')), 15000);
    const buttons = await driver.findElements(By.css('button'));
    console.log('button count', buttons.length);
    for (let i = 0; i < buttons.length; i++) {
      const outer = await buttons[i].getAttribute('outerHTML');
      const text = await buttons[i].getText();
      console.log(`button ${i}: text="${text}" outer="${outer}"`);
    }
    const submit = await driver.findElement(By.id('login-submit-btn'));
    const email = await driver.findElement(By.id('login-email'));
    const password = await driver.findElement(By.id('login-password'));
    await email.clear();
    await password.clear();
    await email.sendKeys('invaliduser@example.com');
    await password.sendKeys('wrong-password');
    await submit.click();
    await driver.sleep(1500);
    const errors = await driver.findElements(By.xpath("//div[contains(text(), 'Please fill in all fields') or contains(text(), 'Login failed') or contains(text(), 'Cannot connect') or contains(text(), 'Google Sign-In failed') or contains(text(), 'Invalid credentials') or contains(text(), 'Email and password are required') or contains(text(), 'Cannot connect to server') or contains(text(), 'Cannot connect to server. Please ensure the backend is running.') ]"));
    console.log('error count', errors.length);
    for (let i = 0; i < errors.length; i++) {
      console.log(`error ${i}: ${await errors[i].getText()}`);
    }
  } catch (err) {
    console.error(err);
  } finally {
    await driver.quit();
  }
})();
