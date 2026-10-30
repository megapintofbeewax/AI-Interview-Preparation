# Prep AI Platform Stopper (PowerShell)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      PREP AI - Stopping Local Host Servers             " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Stop Backend on port 8000
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $port8000 | ForEach-Object { 
        try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
    Write-Host "[✓] Backend on port 8000 stopped." -ForegroundColor Green
} else {
    Write-Host "[-] No process listening on port 8000." -ForegroundColor Gray
}

# Stop Frontend on port 5173
$port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
if ($port5173) {
    $port5173 | ForEach-Object { 
        try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
    Write-Host "[✓] Frontend on port 5173 stopped." -ForegroundColor Green
} else {
    Write-Host "[-] No process listening on port 5173." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Both servers stopped successfully!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
