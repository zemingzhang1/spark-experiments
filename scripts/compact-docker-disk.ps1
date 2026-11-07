# Compacts Docker Desktop's WSL data disk so Windows reclaims the freed space.
# Run from an ELEVATED PowerShell:  powershell -ExecutionPolicy Bypass -File <this file>

$ErrorActionPreference = 'Stop'
$vhdx = Join-Path $env:LOCALAPPDATA 'Docker\wsl\disk\docker_data.vhdx'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This needs Administrator. Re-open PowerShell as admin and run it again." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $vhdx)) { Write-Host "Not found: $vhdx" -ForegroundColor Red; exit 1 }

$before = [math]::Round((Get-Item $vhdx).Length / 1GB, 2)
Write-Host "Before: $before GB" -ForegroundColor Cyan

Write-Host "Quitting Docker Desktop..."
Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process 'com.docker.backend', 'com.docker.build' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 5

Write-Host "Shutting down WSL..."
wsl.exe --shutdown
Start-Sleep -Seconds 5

Write-Host "Compacting (this can take a few minutes)..."
$script = @"
select vdisk file="$vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@
$tmp = Join-Path $env:TEMP 'compact_docker.dp'
Set-Content -Path $tmp -Value $script -Encoding ascii
diskpart /s $tmp
Remove-Item $tmp -Force

$after = [math]::Round((Get-Item $vhdx).Length / 1GB, 2)
Write-Host ""
Write-Host "Before : $before GB" -ForegroundColor Cyan
Write-Host "After  : $after GB"  -ForegroundColor Green
Write-Host "Freed  : $([math]::Round($before - $after, 2)) GB" -ForegroundColor Green
Write-Host ""
Write-Host "Start Docker Desktop again when you're ready; your images and volumes are untouched."
