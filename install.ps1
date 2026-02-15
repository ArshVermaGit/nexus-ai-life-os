# NEXUS Global Installer for Windows (PowerShell)

Write-Host "🚀 Installing NEXUS Terminal Intelligence..." -ForegroundColor Cyan

$InstallDir = Get-Location
$PythonCmd = "python"

# Check for python
try {
    & python --version | Out-Null
} catch {
    Write-Host "❌ Error: Python not found. Please install Python." -ForegroundColor Red
    exit
}

# Install requirements
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
& python -m pip install -r requirements.txt

# Create a batch wrapper in a common local path
$BinDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$WrapperPath = "$BinDir\nexus.bat"

Write-Host "🔗 Creating global command 'nexus' in $BinDir..." -ForegroundColor Cyan

$Content = @"
@echo off
cd /d "$InstallDir"
python main.py %*
"@

Set-Content -Path $WrapperPath -Value $Content

Write-Host ""
Write-Host "✅ NEXUS installed successfully!" -ForegroundColor Green
Write-Host "You can now run 'nexus chat', 'nexus search', or 'nexus check' from any terminal." -ForegroundColor Green
Write-Host ""
