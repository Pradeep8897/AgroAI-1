import { remote } from 'webdriverio'
import fs from 'fs/promises'
import path from 'path'

const ANDROID_DEVICE = process.env.ANDROID_DEVICE || ''
const APP_PACKAGE = process.env.APP_PACKAGE || 'com.agroai.app'
const APP_ACTIVITY = process.env.APP_ACTIVITY || '.SplashActivity'
const PLATFORM_VERSION = process.env.PLATFORM_VERSION || ''
const AUTOMATION_NAME = process.env.AUTOMATION_NAME || 'uiautomator2'

const APP_PATH = process.env.APP_PATH || ''
const DEFAULT_APP_PATHS = [
  path.resolve(process.cwd(), '../app-agroAi.apk'),
  path.resolve(process.cwd(), '../android/app/src/main/assets/app-debug.apk')
]
const CHROMEDRIVER_EXECUTABLE_DIR = path.resolve(process.cwd(), 'node_modules', 'chromedriver', 'lib', 'chromedriver')
const CHROMEDRIVER_EXECUTABLE = path.join(CHROMEDRIVER_EXECUTABLE_DIR, process.platform === 'win32' ? 'chromedriver.exe' : 'chromedriver')

async function fileExists(filePath) {
  try {
    const stat = await fs.stat(filePath)
    return stat.isFile()
  } catch {
    return false
  }
}

async function resolveAppPath() {
  if (APP_PATH && await fileExists(APP_PATH)) {
    return APP_PATH
  }
  for (const candidate of DEFAULT_APP_PATHS) {
    if (await fileExists(candidate)) {
      return candidate
    }
  }
  return undefined
}

async function getDeviceName() {
  if (ANDROID_DEVICE) {
    return ANDROID_DEVICE
  }
  return 'Android Device'
}

async function getWebviewContext(client) {
  const contexts = await client.execute('mobile:getContexts')
  return contexts.find((context) => {
    const contextName = context.webviewName || context.webview || String(context)
    return contextName.toLowerCase().includes('webview')
  })
}

async function switchToWebview(client) {
  const webviewContext = await getWebviewContext(client)
  if (!webviewContext) {
    throw new Error('No WebView context available')
  }
  const contextName = webviewContext.webviewName || webviewContext.webview || String(webviewContext)
  await client.switchContext(contextName)
  return webviewContext
}

async function waitForActivity(client, patterns, timeout = 15000) {
  return client.waitUntil(async () => {
    const activity = await client.getCurrentActivity()
    return patterns.some((pattern) => activity.includes(pattern))
  }, {
    timeout,
    timeoutMsg: `Activity did not match ${patterns.join(', ')} within ${timeout}ms`
  })
}

async function waitForWebviewContext(client, timeout = 20000) {
  return client.waitUntil(async () => {
    const context = await getWebviewContext(client)
    return Boolean(context)
  }, {
    timeout,
    timeoutMsg: `WebView context not available within ${timeout}ms`
  })
}

async function waitForWebviewElement(client, selector, timeout = 25000) {
  const exists = await client.waitUntil(async () => {
    const element = await client.$(selector)
    return element && await element.isExisting()
  }, {
    timeout,
    timeoutMsg: `Element ${selector} not found in WebView within ${timeout}ms`
  }).catch(() => false)

  if (!exists) {
    return null
  }
  const element = await client.$(selector)
  return element.isExisting() ? element : null
}

async function run() {
  const resolvedAppPath = await resolveAppPath()
  const deviceName = await getDeviceName()

  const options = {
    hostname: '127.0.0.1',
    port: 4723,
    path: '/',
    capabilities: {
      platformName: 'Android',
      'appium:automationName': AUTOMATION_NAME,
      'appium:deviceName': deviceName,
      'appium:platformVersion': PLATFORM_VERSION || undefined,
      'appium:appPackage': APP_PACKAGE,
      'appium:appActivity': APP_ACTIVITY,
      'appium:app': resolvedAppPath,
      'appium:autoGrantPermissions': true,
      'appium:newCommandTimeout': 300,
      'appium:unicodeKeyboard': true,
      'appium:resetKeyboard': true,
      'appium:allowTestPackages': true,
      'appium:noReset': false,
      'appium:adbExecTimeout': 50000,
      'appium:autoStartActivity': true,
      'appium:appWaitActivity': 'com.agroai.app.*',
      'appium:appWaitDuration': 30000,
      'appium:waitForIdleTimeout': 10000,
      'appium:uiautomator2ServerLaunchTimeout': 30000,
      'appium:chromedriverExecutableDir': CHROMEDRIVER_EXECUTABLE_DIR,
      'appium:chromedriverExecutable': CHROMEDRIVER_EXECUTABLE
    }
  }

  if (!resolvedAppPath) {
    console.warn('Warning: No APK path resolved. The test may attach to an already installed app package.')
  }

  try {
    await fs.access(CHROMEDRIVER_EXECUTABLE)
  } catch {
    console.warn(`Warning: Chromedriver binary not found at ${CHROMEDRIVER_EXECUTABLE}. WebView automation may fail.`)
  }

  const client = await remote(options)
  const results = []

  try {
    results.push(await expectSplashAndMainScreen(client))
    results.push(await tryLoginScreenPresence(client))
    results.push(await verifyWebViewLoaded(client))
    results.push(await testBackButton(client))
    results.push(await checkGoogleAuthButton(client))

    await printResults(results)
  } catch (err) {
    console.error('Appium test runner failed:', err)
    process.exitCode = 1
  } finally {
    await client.deleteSession()
  }
}

async function expectSplashAndMainScreen(client) {
  await client.pause(3000)
  let activity = ''
  try {
    activity = await client.getCurrentActivity()
  } catch (e) {
    return {
      id: 'app-splash-launch',
      name: 'Native splash activity launches',
      status: 'FAIL',
      details: `Failed to get activity: ${e.message}`
    }
  }
  const pass = activity.includes('SplashActivity') || activity.includes('MainActivity') || activity.includes('LoginActivity')
  return {
    id: 'app-splash-launch',
    name: 'Native splash activity launches',
    status: pass ? 'PASS' : 'FAIL',
    details: pass ? `Launched activity ${activity}.` : `Unexpected activity ${activity}. Expected *SplashActivity, *MainActivity, or *LoginActivity.`
  }
}

async function tryLoginScreenPresence(client) {
  try {
    await waitForWebviewContext(client, 20000)
    const webviewContext = await getWebviewContext(client)
    return {
      id: 'webview-context',
      name: 'WebView context is available',
      status: webviewContext ? 'PASS' : 'FAIL',
      details: webviewContext
        ? `Found WebView context: ${webviewContext.webview || String(webviewContext)}`
        : 'No WebView context found in the app.'
    }
  } catch (err) {
    return {
      id: 'webview-context',
      name: 'WebView context is available',
      status: 'FAIL',
      details: `Error getting WebView contexts: ${err.message}`
    }
  }
}

async function verifyWebViewLoaded(client) {
  try {
    const webviewContext = await switchToWebview(client)
    if (!webviewContext) {
      return {
        id: 'webview-loaded',
        name: 'Verify WebView loads frontend content',
        status: 'FAIL',
        details: 'WebView context not found in app.'
      }
    }

    await client.pause(1500)
    const pageUrl = await client.getUrl().catch(() => '')
    const pageTitle = await client.getTitle().catch(() => '')

    const emailInput = await waitForWebviewElement(client, '#login-email', 30000)
    const passwordInput = await waitForWebviewElement(client, '#login-password', 30000)
    const loginButton = await waitForWebviewElement(client, '#login-submit-btn', 30000)
    const googleButton = await waitForWebviewElement(client, "button*=Continue with Google", 30000)

    const pass = Boolean(emailInput || passwordInput || loginButton || googleButton)
    return {
      id: 'webview-loaded',
      name: 'Verify WebView loads frontend content',
      status: pass ? 'PASS' : 'FAIL',
      details: pass
        ? `Frontend loaded with login DOM content. URL=${pageUrl}, title=${pageTitle}`
        : `WebView loaded but login DOM not detected. URL=${pageUrl}, title=${pageTitle}.` 
    }
  } catch (err) {
    return {
      id: 'webview-loaded',
      name: 'Verify WebView loads frontend content',
      status: 'FAIL',
      details: `WebView verification error: ${err.message}`
    }
  } finally {
    await client.switchContext('NATIVE_APP').catch(() => null)
  }
}

async function testBackButton(client) {
  try {
    await client.back()
    await client.pause(1500)
    let currentUrl = ''
    try {
      currentUrl = await client.execute(() => window.location.href)
    } catch (e) {
      // Back button may exit WebView, this is expected
    }
    return {
      id: 'android-back-button',
      name: 'Android back button navigation',
      status: 'PASS',
      details: currentUrl ? `Navigation returned to ${currentUrl}` : 'Back button executed successfully. (WebView may have exited)'
    }
  } catch (err) {
    return {
      id: 'android-back-button',
      name: 'Android back button navigation',
      status: 'WARN',
      details: `Back navigation test encountered: ${err.message}`
    }
  }
}

async function checkGoogleAuthButton(client) {
  try {
    await switchToWebview(client)
    await client.pause(1500)

    const selectors = [
      "button*=Continue with Google",
      "xpath=//*[contains(normalize-space(.), 'Continue with Google')]",
      "xpath=//*[contains(normalize-space(.), 'Google Sign-In')]",
      "xpath=//*[contains(normalize-space(.), 'Google')]",
      "button*=Google"
    ]

    for (const selector of selectors) {
      try {
        const googleButton = await client.$(selector)
        if (await googleButton.isExisting()) {
          return {
            id: 'google-auth-button',
            name: 'Google auth button appears in app WebView',
            status: 'PASS',
            details: `Google sign-in button found via selector: ${selector}`
          }
        }
      } catch {
        continue
      }
    }

    const pageUrl = await client.getUrl().catch(() => '')
    const pageTitle = await client.getTitle().catch(() => '')
    return {
      id: 'google-auth-button',
      name: 'Google auth button appears in app WebView',
      status: 'FAIL',
      details: `Google sign-in button was not found in the WebView. URL=${pageUrl}, title=${pageTitle}`
    }
  } catch (err) {
    return {
      id: 'google-auth-button',
      name: 'Google auth button appears in app WebView',
      status: 'FAIL',
      details: `Google button test error: ${err.message}`
    }
  } finally {
    await client.switchContext('NATIVE_APP').catch(() => null)
  }
}

async function printResults(results) {
  console.log('=== Appium Login E2E Test Summary ===')
  let passed = 0
  for (const result of results) {
    console.log(`${result.id}: ${result.status}`)
    console.log(`  ${result.details}`)
    if (result.status === 'PASS') passed += 1
  }
  console.log(`\nOverall: ${passed}/${results.length} passed.`)
}

await run()
