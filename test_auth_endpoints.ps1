# PowerShell script to test JWT authentication endpoints
$BaseURL = "http://127.0.0.1:5000"
$email = "testuser@agroai.com"
$password = "TestPass123"
$name = "Test User"

Write-Host "=== STEP 0: Register User ===" -ForegroundColor Cyan

$registerBody = @{
    username = $name
    email = $email
    password = $password
    role = "farmer"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "$BaseURL/api/auth/register" -Method POST -ContentType "application/json" -Body $registerBody
    Write-Host "Registration response:" -ForegroundColor Green
    $registerResponse | ConvertTo-Json | Write-Host
} catch {
    Write-Host "Registration attempt (may already exist): $_" -ForegroundColor Yellow
}

Write-Host "`n=== STEP 1: Login and Get Token ===" -ForegroundColor Cyan

$loginBody = @{
    email = $email
    password = $password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BaseURL/api/auth/login" -Method POST -ContentType "application/json" -Body $loginBody
    Write-Host "Success! Login response:" -ForegroundColor Green
    $loginResponse | ConvertTo-Json | Write-Host
    $token = $loginResponse.token
    if (-not $token) {
        Write-Host "ERROR: No token in response!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Token: $($token.Substring(0, 30))..." -ForegroundColor Green
} catch {
    Write-Host "ERROR during login: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== STEP 2: Access Protected Endpoint WITH Token ===" -ForegroundColor Cyan

try {
    $headers = @{"Authorization" = "Bearer $token"}
    $profileResponse = Invoke-RestMethod -Uri "$BaseURL/api/auth/profile" -Method GET -Headers $headers
    Write-Host "Success! Profile response:" -ForegroundColor Green
    $profileResponse | ConvertTo-Json | Write-Host
} catch {
    Write-Host "ERROR accessing profile: $_" -ForegroundColor Red
}

Write-Host "`n=== STEP 3: Access Protected Endpoint WITHOUT Token (Should Fail) ===" -ForegroundColor Yellow

try {
    $noTokenResponse = Invoke-RestMethod -Uri "$BaseURL/api/auth/profile" -Method GET -ErrorAction Stop
    Write-Host "ERROR: Access allowed without token!" -ForegroundColor Red
} catch {
    Write-Host "Good! Request rejected as expected (Status: $($_.Exception.Response.StatusCode))" -ForegroundColor Green
}


Write-Host "`n=== STEP 4: Test Crop Recommendation Endpoint ===" -ForegroundColor Cyan

$cropBody = @{
    nitrogen = 50
    phosphorus = 40
    potassium = 30
    ph = 6.5
    rainfall = 100
    temperature = 28
} | ConvertTo-Json

try {
    $headers = @{"Authorization" = "Bearer $token"}
    $cropResponse = Invoke-RestMethod -Uri "$BaseURL/api/crop/recommend" -Method POST -Headers $headers -ContentType "application/json" -Body $cropBody
    Write-Host "Success! Crop response:" -ForegroundColor Green
    $cropResponse | ConvertTo-Json | Write-Host
} catch {
    Write-Host "ERROR accessing crop endpoint: $_" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
