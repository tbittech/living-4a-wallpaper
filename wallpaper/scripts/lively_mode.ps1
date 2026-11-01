# Cambia la entrada "Living 4A" de Lively entre la demo y Claude real, y la vuelve a poner de fondo.
# live: Lively abre public\index.html como archivo local (tipo web), así el fondo anda aunque server.py no esté;
# la página se conecta sola a 127.0.0.1:8765 cuando el servidor aparece (lo arranca el hook de Claude).
# demo: URL del servidor (necesita server.py corriendo).
#   powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\lively_mode.ps1 live
#   powershell -NoProfile -ExecutionPolicy Bypass -File wallpaper\scripts\lively_mode.ps1 demo
#   ... lively_mode.ps1 live -Debug1   (agrega ?debug=1: estado de la conexión y teclas del simulador)
param(
    [Parameter(Mandatory = $true)][ValidateSet("live", "demo")][string]$Mode,
    [switch]$Debug1
)

$dir = Join-Path $env:LOCALAPPDATA "Lively Wallpaper\Library\wallpapers\bbt_living4a"
$info = Join-Path $dir "LivelyInfo.json"
$lively = @("$env:ProgramFiles\Lively Wallpaper\Lively.exe", "$env:LOCALAPPDATA\Programs\Lively Wallpaper\Lively.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $lively) { throw "No encontré Lively.exe (¿está instalado?)" }

$index = (Resolve-Path (Join-Path $PSScriptRoot "..\public\index.html")).Path

if ($Mode -eq "live" -and -not $Debug1) {
    $url = $index
    $type = 1   # WallpaperType.web: archivo local
} else {
    # Con -Debug1 en live hace falta la URL (un archivo local no lleva ?debug=1)
    $url = $(if ($Mode -eq "demo") { "http://127.0.0.1:8765/?demo=1&sources=claude,codex,gemini" } else { "http://127.0.0.1:8765/" })
    if ($Debug1) { $url += $(if ($url.Contains("?")) { "&debug=1" } else { "?debug=1" }) }
    $type = 3   # WallpaperType.url
}

$json = Get-Content $info -Raw | ConvertFrom-Json
$json.FileName = $url
$json.Type = $type
$json.IsAbsolutePath = $true
# Sin BOM: Lively lee el json con System.Text.Json
[System.IO.File]::WriteAllText($info, ($json | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding $false))

& $lively setwp --file $dir
Write-Output "Lively -> $url"
