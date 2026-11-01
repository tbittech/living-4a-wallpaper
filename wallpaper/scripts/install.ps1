# Instala el wallpaper Living 4A en esta PC, desde donde esté la carpeta (no importa el disco ni la ruta).
# Lo normal es hacer doble clic en wallpaper\install.bat. Se puede correr de nuevo sin problema (por ejemplo después de
# mover la carpeta): actualiza las rutas.
#   1. Python (si no está, ofrece instalarlo con winget) y aiohttp para el servidor.
#   2. Hooks de Claude Code en %USERPROFILE%\.claude\settings.json (hooks_setup.py; deja los demás hooks como están).
#   3. Lively Wallpaper (si no está, ofrece instalarlo) con la entrada "Living 4A" puesta de fondo.
#   4. Servidor en Inicio de Windows (install_startup.ps1) y lo arranca ya.
#   ... install.ps1 -NoLively -NoStartup -Settings X.json   (pruebas)
param([switch]$NoLively, [switch]$NoStartup, [string]$Settings)

# Continue y no Stop: en PowerShell 5.1 cualquier línea de stderr de python o pip cortaría todo
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Ask($q) { (Read-Host "$q [S/n]") -notmatch '^[nN]' }

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

# El python.exe real (no el alias de la Store, que existe pero abre la tienda)
function Find-Python {
    foreach ($cand in @(@("python"), @("py", "-3"))) {
        if (-not (Get-Command $cand[0] -ErrorAction SilentlyContinue)) { continue }
        $a = @($cand | Select-Object -Skip 1) + @("-c", "import sys; print(sys.executable)")
        try { $exe = & $cand[0] @a 2>$null } catch { continue }
        if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) { return $exe.Trim() }
    }
    return $null
}

function Find-Lively {
    foreach ($p in @("$env:ProgramFiles\Lively Wallpaper\Lively.exe", "$env:LOCALAPPDATA\Programs\Lively Wallpaper\Lively.exe")) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

Write-Output "== Living 4A: instalando desde $root"

# 1. Python + aiohttp
$py = Find-Python
if (-not $py) {
    if (-not (Ask "No encontré Python. ¿Lo instalo con winget?")) { throw "Hace falta Python 3 (python.org)." }
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    Refresh-Path
    $py = Find-Python
    if (-not $py) { throw "Python quedó instalado pero no lo encuentro: cerrá esta ventana y corré install.bat de nuevo." }
}
Write-Output "Python: $py"
& $py -c "import aiohttp" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Output "Instalando aiohttp..."
    & $py -m pip install --user --disable-pip-version-check aiohttp
    if ($LASTEXITCODE -ne 0) { throw "No se pudo instalar aiohttp." }
}

# 2. Hooks de Claude Code
$hookArgs = @((Join-Path $PSScriptRoot "hooks_setup.py"), "install")
if ($Settings) { $hookArgs += @("--settings", $Settings) }
& $py @hookArgs
if ($LASTEXITCODE -ne 0) { throw "No se pudieron poner los hooks." }

# 3. Lively
if (-not $NoLively) {
    $lively = Find-Lively
    if (-not $lively -and (Ask "No encontré Lively Wallpaper. ¿Lo instalo con winget?")) {
        winget install -e --id rocksdanister.LivelyWallpaper --accept-source-agreements --accept-package-agreements
        $lively = Find-Lively
    }
    if ($lively) {
        $dir = Join-Path $env:LOCALAPPDATA "Lively Wallpaper\Library\wallpapers\bbt_living4a"
        New-Item -ItemType Directory -Force $dir | Out-Null
        Copy-Item (Join-Path $PSScriptRoot "lively_thumbnail.jpg") (Join-Path $dir "thumbnail.jpg") -Force
        $info = [ordered]@{
            AppVersion = "2.0.7.4"; Title = "Living 4A"; Thumbnail = "thumbnail.jpg"; Preview = $null
            Desc = "Big Bang: Sheldon, Leonard y Penny siguen a Claude, Codex y Gemini (servidor en 127.0.0.1:8765)."
            Author = "ProyectosIA"; License = $null; Contact = $null
            Type = 1; FileName = (Join-Path $root "public\index.html"); Arguments = $null; IsAbsolutePath = $true
        }
        # Sin BOM: Lively lee el json con System.Text.Json
        [System.IO.File]::WriteAllText((Join-Path $dir "LivelyInfo.json"), ($info | ConvertTo-Json), (New-Object System.Text.UTF8Encoding $false))
        & (Join-Path $PSScriptRoot "lively_mode.ps1") live
    } else {
        Write-Output "Sin Lively: el living se puede ver igual en http://127.0.0.1:8765/ con el servidor andando."
    }
}

# 4. Inicio de Windows + servidor ya
if (-not $NoStartup) {
    & (Join-Path $PSScriptRoot "install_startup.ps1") -Python $py
    if (-not (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue)) {
        $server = Join-Path $root "server\server.py"
        Start-Process (Join-Path (Split-Path $py) "pythonw.exe") -ArgumentList "`"$server`"", "--quiet" -WorkingDirectory (Split-Path $server)
        Write-Output "Servidor arrancado en 127.0.0.1:8765"
    }
}

Write-Output "== Listo. Abrí (o reiniciá) Claude Code para que tome los hooks."
