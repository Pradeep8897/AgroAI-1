import { Builder, By, until } from 'selenium-webdriver'
import chrome from 'selenium-webdriver/chrome.js'

const FRONTEND_URL = 'http://127.0.0.1:5173'
const BACKEND_URL = 'http://127.0.0.1:5000'

;(async () => {
  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(new chrome.Options().addArguments('--headless=new', '--disable-gpu', '--window-size=1280,1024'))
    .build()

  try {
    await driver.get(`${FRONTEND_URL}/login`)
    await driver.executeScript("localStorage.setItem('agroai_backend_url', arguments[0])", BACKEND_URL)
    await driver.navigate().refresh()
    await driver.wait(until.elementLocated(By.id('login-email')), 20000)
    const src = await driver.getPageSource()
    const idx = src.indexOf('id="login-email"')
    console.log('login-email index', idx)
    console.log(src.slice(Math.max(0, idx-200), idx+200))
    const idx2 = src.indexOf('id="login-password"')
    console.log('login-password index', idx2)
    console.log(src.slice(Math.max(0, idx2-200), idx2+200))
    const idx3 = src.indexOf('id="login-submit-btn"')
    console.log('login-submit-btn index', idx3)
    console.log(src.slice(Math.max(0, idx3-200), idx3+200))
    const email = await driver.findElement(By.id('login-email'))
    console.log('found element after page source', await email.getAttribute('outerHTML'))
  } catch (err) {
    console.error(err)
  } finally {
    await driver.quit()
  }
})()
