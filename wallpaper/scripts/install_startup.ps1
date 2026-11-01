# Pone (o saca) el servidor del wallpaper en Inicio de Windows: así, si prendés OmniRoute antes de abrir Claude Code,
# Leonard y Penny aparecen igual. Sin esto el servidor lo arranca el hook de Claude Code la primera vez que se usa.
#   powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\install_startup.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\install_startup.ps1 -Remove
#   ... install_startup.ps1 -Python C:\ruta\python.exe   (install.ps1 le pasa el que encontró)
param([switch]$Remove, [string]$Python)

$lnk = Join-Path ([Environment]::GetFolderPath("Startup")) "Living 4A server.lnk"
if ($Remove) {
    Remove-Item $lnk -ErrorAction SilentlyContinue
    Write-Output "Sacado: $lnk"
    return
}

$python = $(if ($Python) { $Python } else { (Get-Command python).Source })
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
$server = (Resolve-Path (Join-Path $PSScriptRoot "..\server\server.py")).Path

$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath = $pythonw
$s.Arguments = "`"$server`" --quiet"
$s.WorkingDirectory = Split-Path $server
$s.Description = "Servidor del wallpaper Living 4A (Lively)"
$s.Save()
Write-Output "Puesto: $lnk"
