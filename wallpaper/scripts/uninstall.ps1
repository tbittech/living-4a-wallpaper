# Deshace install.ps1: saca los hooks de Claude Code, el acceso de Inicio, la entrada de Lively y frena el servidor.
# No borra la carpeta del proyecto ni desinstala Python o Lively. Doble clic en wallpaper\uninstall.bat.
#   ... uninstall.ps1 -Settings X.json   (pruebas: otro settings.json)
param([string]$Settings)

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# Hooks: con el python que figure en el propio hook, o el del PATH
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if ($py) {
    $hookArgs = @((Join-Path $PSScriptRoot "hooks_setup.py"), "remove")
    if ($Settings) { $hookArgs += @("--settings", $Settings) }
    & $py @hookArgs
} else {
    Write-Output "Sin Python: sacá a mano de %USERPROFILE%\.claude\settings.json los hooks que llaman a cc_hook.py"
}
if ($Settings) { return }

& (Join-Path $PSScriptRoot "install_startup.ps1") -Remove

# Servidor
Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
    Where-Object { $_.CommandLine -like "*$root\server\server.py*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Output "Servidor frenado (pid $($_.ProcessId))" }

# Lively
$lively = @("$env:ProgramFiles\Lively Wallpaper\Lively.exe", "$env:LOCALAPPDATA\Programs\Lively Wallpaper\Lively.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($lively) { & $lively closewp -m -1 }
$dir = Join-Path $env:LOCALAPPDATA "Lively Wallpaper\Library\wallpapers\bbt_living4a"
if (Test-Path $dir) { Remove-Item $dir -Recurse -Force; Write-Output "Entrada de Lively sacada" }

Write-Output "== Desinstalado. La carpeta del proyecto queda como está."
