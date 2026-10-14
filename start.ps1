$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path $pythonPath) -or !(Test-Path 'node_modules')) {
    throw 'Faltan dependencias. Ejecuta primero: powershell -ExecutionPolicy Bypass -File .\setup.ps1'
}
foreach ($port in @(8000, 5173)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "El puerto $port está ocupado. Cierra el servidor anterior antes de iniciar FitAdaptAI."
    }
}
$backend = Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn api.index:app --host 127.0.0.1 --port 8000' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'backend.log' -RedirectStandardError 'backend-error.log'
try {
    Write-Host 'FitAdaptAI: http://127.0.0.1:5173 · Ctrl+C para detener.'
    & npm.cmd run dev
} finally {
    if (!$backend.HasExited) { Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue }
}
