// apiConfig.js - Dynamically determine the backend API base URL
// When running in the Android WebView app, checks for user configurations in localStorage,
// queries the native Java bridge (AndroidBridge) for the backend URL, or falls back to local loopback (10.0.2.2).

export const getApiBase = () => {
  const ensureApiSuffix = (url) => {
    if (!url) return '/api';
    const trimmed = url.trim().replace(/\/+$/, '');
    if (trimmed.endsWith('/api')) {
      return trimmed;
    }
    return `${trimmed}/api`;
  };

  // 1. First priority: Check if user configured a custom backend server address in Settings
  try {
    const savedUrl = localStorage.getItem('agroai_backend_url');
    if (savedUrl && savedUrl.trim() !== '') {
      return ensureApiSuffix(savedUrl);
    }
  } catch (e) {
    console.error("Failed to read backend URL from localStorage:", e);
  }

  // 2. Second priority: Query dynamic value from Kotlin bridge if connected
  if (window.AndroidBridge && typeof window.AndroidBridge.getBackendUrl === 'function') {
    try {
      const bridgeUrl = window.AndroidBridge.getBackendUrl();
      if (bridgeUrl && bridgeUrl !== "https://YOUR_DEPLOYED_URL") {
        return ensureApiSuffix(bridgeUrl);
      }
    } catch (e) {
      console.error("Failed to fetch backend URL from Android Bridge:", e);
    }
  }
  
  // 3. Third priority: Standalone Android App default local loopback for emulator testing
  if (navigator.userAgent.includes('AgroAI-Android')) {
    return 'https://agroai-9ibe.onrender.com/api';
  }

  // 4. Fourth priority: Local development fallback when running the frontend locally
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || import.meta.env.DEV) {
    return 'http://127.0.0.1:5000/api';
  }
  
  // 5. Fifth priority: Fallback for development server environment variables
  const envBase = import.meta.env.VITE_API_BASE;
  if (envBase) {
    return ensureApiSuffix(envBase);
  }
  
  // 6. Ultimate default fallback
  return 'https://agroai-9ibe.onrender.com/api';
};

export const API_BASE = getApiBase();

