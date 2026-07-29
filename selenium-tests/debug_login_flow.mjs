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
    console.log('navigate to login')
    await driver.get(`${FRONTEND_URL}/login`)
    console.log('set backend localStorage')
    await driver.executeScript("localStorage.setItem('agroai_backend_url', arguments[0])", BACKEND_URL)
    console.log('refresh page')
    await driver.navigate().refresh()
    console.log('waiting for login-email')
    const email = await driver.wait(until.elementLocated(By.id('login-email')), 20000)
    console.log('found email element', await email.getAttribute('outerHTML'))
    const pageSource = await driver.getPageSource()
    console.log('page source length', pageSource.length)
  } catch (err) {
    console.error(err)
    try {
      const src = await driver.getPageSource()
      console.log('current page source length:', src.length)
      console.log(src.slice(0, 2000))
    } catch (innerErr) {
      console.error('failed to get page source', innerErr)
    }
  } finally {
    await driver.quit()
  }
})()
