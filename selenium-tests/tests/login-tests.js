import { Builder, By, until } from 'selenium-webdriver'
import chrome from 'selenium-webdriver/chrome.js'

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:5173'
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:5000'
const VALID_EMAIL = process.env.TEST_EMAIL || 'selenium_test_user@agroai.com'
const VALID_PASSWORD = process.env.TEST_PASSWORD || 'TestPassword123!'
const INVALID_EMAIL = process.env.TEST_EMAIL_INVALID || 'invaliduser@example.com'
const INVALID_PASSWORD = process.env.TEST_PASSWORD_INVALID || 'wrong-password'

async function ensureLocalBackendConfigured(driver) {
  console.log('Navigating to login page...')
  await driver.get(`${FRONTEND_URL}/login`)
  console.log('Setting backend URL in localStorage...')
  await driver.executeScript("localStorage.setItem('agroai_backend_url', arguments[0])", BACKEND_URL)
  console.log('Refreshing page after backend config...')
  await driver.navigate().refresh()
  console.log('Waiting for login email field after refresh...')
  try {
    await driver.wait(until.elementLocated(By.id('login-email')), 30000)
    console.log('Login email field found after refresh.')
  } catch (err) {
    console.error('Failed to locate login email after refresh. URL:', await driver.getCurrentUrl())
    const pageSource = await driver.getPageSource()
    console.error('Page source contains login-email:', pageSource.includes('id="login-email"'))
    console.error('Page source length after failure:', pageSource.length)
    console.error('Page source excerpt:', pageSource.slice(0, 2000))
    throw err
  }
}

async function ensureTestUserExists() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: 'Selenium Test User',
        email: VALID_EMAIL,
        password: VALID_PASSWORD
      })
    })
    const data = await response.json()
    return data.success === true || (data.message && data.message.toLowerCase().includes('already registered'))
  } catch (err) {
    console.warn('Unable to ensure test user exists:', err)
    return false
  }
}

async function waitForLocator(driver, locator, timeout = 30000) {
  console.log(`Waiting for locator ${locator} up to ${timeout}ms`)
  const success = await driver.wait(async () => {
    const elems = await driver.findElements(locator)
    const count = elems.length
    if (count > 0) {
      console.log(`Found ${count} elements for locator ${locator}`)
      return true
    }
    return false
  }, timeout).catch(() => false)
  return success
}

async function runLoginTests() {
  const options = new chrome.Options()
  options.addArguments('--headless=new', '--disable-gpu', '--window-size=1280,1024')

  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build()

  const results = []

  try {
    console.log('Ensuring test user exists...')
    await ensureTestUserExists()
    console.log('Configuring local backend in browser...')
    await ensureLocalBackendConfigured(driver)
    console.log('Local backend configured, checking page state...')

    console.log('Current URL:', await driver.getCurrentUrl())
    const pageSource = await driver.getPageSource()
    console.log('Page source contains login-email:', pageSource.includes('id="login-email"'))
    console.log('Page source contains login-password:', pageSource.includes('id="login-password"'))
    console.log('Page source contains login-submit-btn:', pageSource.includes('id="login-submit-btn"'))

    const emailReady = await waitForLocator(driver, By.id('login-email'), 30000)
    const passwordReady = await waitForLocator(driver, By.id('login-password'), 30000)
    const submitReady = await waitForLocator(driver, By.id('login-submit-btn'), 30000)

    if (!emailReady || !passwordReady || !submitReady) {
      throw new Error('Login form elements not available after waiting')
    }

    results.push(await testLoginPageElements(driver))
    results.push(await testEmptyFormValidation(driver))
    results.push(await testInvalidCredentials(driver))
    results.push(await testGoogleSignInButton(driver))
    results.push(await testSuccessfulLogin(driver))

    await printResults(results)
  } catch (error) {
    console.error('Test runner encountered an error:', error)
    process.exitCode = 1
  } finally {
    await driver.quit()
  }
}

async function testLoginPageElements(driver) {
  const email = await driver.findElement(By.id('login-email'))
  const password = await driver.findElement(By.id('login-password'))
  const submit = await driver.findElement(By.id('login-submit-btn'))

  const valid = email && password && submit
  return {
    id: 'login-page-elements',
    name: 'Login page elements are present',
    status: valid ? 'PASS' : 'FAIL',
    details: valid
      ? 'Email, password and submit button are visible on the login page.'
      : 'One or more login controls are missing from the login page.'
  }
}

async function testEmptyFormValidation(driver) {
  const submit = await driver.findElement(By.id('login-submit-btn'))
  await submit.click()

  const errorText = await getVisibleErrorText(driver)
  const pass = errorText?.includes('Please fill in all fields.')

  return {
    id: 'empty-form-validation',
    name: 'Empty login form validation',
    status: pass ? 'PASS' : 'FAIL',
    details: pass
      ? 'The login form displays validation text when email and password are empty.'
      : `Expected empty-form validation message, got: ${errorText}`
  }
}

async function testInvalidCredentials(driver) {
  const email = await driver.findElement(By.id('login-email'))
  const password = await driver.findElement(By.id('login-password'))
  const submit = await driver.findElement(By.id('login-submit-btn'))

  await email.clear()
  await email.sendKeys(INVALID_EMAIL)
  await password.clear()
  await password.sendKeys(INVALID_PASSWORD)
  await submit.click()

  const errorText = await getVisibleErrorText(driver)
  const pass = errorText && /login failed|cannot connect|incorrect|invalid credentials/i.test(errorText)

  return {
    id: 'invalid-credentials',
    name: 'Login rejects invalid credentials',
    status: pass ? 'PASS' : 'FAIL',
    details: pass
      ? 'The login form rejected invalid credentials with an error message.'
      : `Expected invalid credentials error, got: ${errorText}`
  }
}

async function testSuccessfulLogin(driver) {
  const email = await driver.findElement(By.id('login-email'))
  const password = await driver.findElement(By.id('login-password'))
  const submit = await driver.findElement(By.id('login-submit-btn'))

  await email.clear()
  await email.sendKeys(VALID_EMAIL)
  await password.clear()
  await password.sendKeys(VALID_PASSWORD)
  await submit.click()

  const navSuccess = await driver.wait(
    until.urlContains('/dashboard'),
    15000
  ).catch(() => null)

  const pass = Boolean(navSuccess)
  return {
    id: 'successful-login',
    name: 'Valid login redirects to dashboard',
    status: pass ? 'PASS' : 'FAIL',
    details: pass
      ? 'Successful login redirected the user to the dashboard.'
      : 'Login did not redirect to dashboard with valid credentials.'
  }
}

async function clearAuthState(driver) {
  await driver.executeScript("localStorage.removeItem('agroai_token'); localStorage.removeItem('agroai_user');")
}

async function testGoogleSignInButton(driver) {
  await clearAuthState(driver)
  await ensureLocalBackendConfigured(driver)

  const googleButtons = await driver.findElements(By.xpath("//button[contains(normalize-space(.), 'Continue with Google') or contains(normalize-space(.), 'Sign in with Google') or contains(normalize-space(.), 'Google')]"))
  const pass = googleButtons.length > 0

  return {
    id: 'google-signin-button',
    name: 'Google sign-in button is visible',
    status: pass ? 'PASS' : 'FAIL',
    details: pass
      ? 'The Google sign-in button is present on the login page.'
      : 'Could not find the Google sign-in button on the login page.'
  }
}

async function getVisibleErrorText(driver) {
  const errorXPath = "//div[contains(text(), 'Please fill in all fields') or contains(text(), 'Invalid credentials') or contains(text(), 'Login failed') or contains(text(), 'Cannot connect') or contains(text(), 'Google Sign-In failed')]"
  await driver.wait(async () => {
    const errorDivs = await driver.findElements(By.xpath(errorXPath))
    return errorDivs.length > 0
  }, 10000).catch(() => null)

  const errorDivs = await driver.findElements(By.xpath(errorXPath))
  if (errorDivs.length > 0) {
    return await errorDivs[0].getText()
  }
  return ''
}

async function printResults(results) {
  console.log('=== Selenium Login Test Results ===')
  let passed = 0
  for (const result of results) {
    console.log(`${result.id}: ${result.status}`)
    console.log(`  ${result.details}`)
    if (result.status === 'PASS') passed += 1
  }
  console.log(`\nSummary: ${passed}/${results.length} tests passed.`)
}

await runLoginTests()
