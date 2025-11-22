# Official Website Verifier - API Test Script

Write-Host "`n" -NoNewline
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Official Website Verification Platform - API Tests" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "[Test 1] Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_URL/health" -Method GET
    Write-Host "  ✓ Status: $($health.status)" -ForegroundColor Green
    Write-Host "  ✓ Mode: $($health.mode)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Lookup HDFC Bank
Write-Host "[Test 2] Lookup HDFC Bank..." -ForegroundColor Yellow
try {
    $hdfc = Invoke-RestMethod -Uri "$API_URL/v1/lookup" -Method POST -ContentType "application/json" -Body '{"query": "HDFC Bank"}'
    Write-Host "  ✓ Name: $($hdfc.data.name)" -ForegroundColor Green
    Write-Host "  ✓ Domain: $($hdfc.data.official_domain)" -ForegroundColor Green
    Write-Host "  ✓ Confidence Score: $($hdfc.data.confidence_score)" -ForegroundColor Green
    Write-Host "  ✓ Risk Level: $($hdfc.data.risk_level)" -ForegroundColor Green
    Write-Host "  ✓ Verification Sources: $($hdfc.data.verification_sources.Count)" -ForegroundColor Green
    Write-Host "  ✓ Similar Domains Found: $($hdfc.data.similar_domains.Count)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Lookup PayPal
Write-Host "[Test 3] Lookup PayPal..." -ForegroundColor Yellow
try {
    $paypal = Invoke-RestMethod -Uri "$API_URL/v1/lookup" -Method POST -ContentType "application/json" -Body '{"query": "PayPal"}'
    Write-Host "  ✓ Name: $($paypal.data.name)" -ForegroundColor Green
    Write-Host "  ✓ Domain: $($paypal.data.official_domain)" -ForegroundColor Green
    Write-Host "  ✓ Confidence Score: $($paypal.data.confidence_score)" -ForegroundColor Green
    Write-Host "  ✓ Risk Level: $($paypal.data.risk_level)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Check Known Domain
Write-Host "[Test 4] Check Known Domain (google.com)..." -ForegroundColor Yellow
try {
    $check = Invoke-RestMethod -Uri "$API_URL/v1/domains/check" -Method POST -ContentType "application/json" -Body '{"domain": "google.com"}'
    Write-Host "  ✓ Domain: $($check.domain)" -ForegroundColor Green
    Write-Host "  ✓ Known: $($check.known)" -ForegroundColor Green
    Write-Host "  ✓ Entity: $($check.entity_name)" -ForegroundColor Green
    Write-Host "  ✓ Score: $($check.confidence_score)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: Check Unknown Domain
Write-Host "[Test 5] Check Unknown Domain (suspicious-bank.com)..." -ForegroundColor Yellow
try {
    $unknown = Invoke-RestMethod -Uri "$API_URL/v1/domains/check" -Method POST -ContentType "application/json" -Body '{"domain": "suspicious-bank.com"}'
    Write-Host "  ✓ Domain: $($unknown.domain)" -ForegroundColor Green
    Write-Host "  ✓ Known: $($unknown.known)" -ForegroundColor Green
    Write-Host "  ✓ Risk Level: $($unknown.risk_level)" -ForegroundColor Green
    Write-Host "  ✓ Message: $($unknown.message)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 6: Submit Domain
Write-Host "[Test 6] Submit Domain for Verification..." -ForegroundColor Yellow
try {
    $body = @{
        submitted_by = "test@example.com"
        entity_name = "Test Company"
        domain = "testcompany.com"
        evidence = @{note = "Official website"}
    } | ConvertTo-Json
    $submission = Invoke-RestMethod -Uri "$API_URL/v1/submissions" -Method POST -ContentType "application/json" -Body $body
    Write-Host "  ✓ Submission ID: $($submission.submission_id)" -ForegroundColor Green
    Write-Host "  ✓ Status: $($submission.status)" -ForegroundColor Green
    Write-Host "  ✓ Message: $($submission.message)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  All Tests Completed!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "🌐 Demo UI: Open demo.html in your browser" -ForegroundColor White
Write-Host ""
