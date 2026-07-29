import { Builder, By, until } from 'selenium-webdriver'
import chrome from 'selenium-webdriver/chrome.js'

const FRONTEND_URL = 'http://127.0.0.1:5173'
const BACKEND_URL = 'http://127.0.0.1:5000'

async function setupLogin(driver) {
  await driver.get(`${FRONTEND_URL}/login`)
  await driver.executeScript("localStorage.setItem('agroai_backend_url', arguments[0])", BACKEND_URL)
  await driver.navigate().refresh()
  await driver.wait(until.elementLocated(By.id('login-email')), 20000)
  console.log('setupLogin succeeded: url', await driver.getCurrentUrl())
}

(async () => {
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(new chrome.Options().addArguments('--headless=new', '--disable-gpu', '--window-size=1280,1024'))
    .build()
  try {
    console.log('First setup')
    await setupLogin(driver)
    console.log('Doing second setup')
    await setupLogin(driver)
    console.log('Second setup succeeded')
  } catch (err) {
    console.error('Error during double setup:', err)
    console.log('Current URL after error:', await driver.getCurrentUrl())
    const src = await driver.getPageSource()
    console.log('Page source length after error', src.length)
    console.log(src.slice(0, 1200))
  } finally {
    await driver.quit()
  }
})()
