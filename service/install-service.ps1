# User-level persistence on Windows (no admin): a hidden launcher in the user's Startup folder
# that serves ~/portfolio/dist on 127.0.0.1:8787 at logon, then starts it now.
# Remove with service/uninstall-service.ps1.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
# python.exe, not pythonw.exe: under pythonw sys.stderr is None and http.server's request
# logging raises, dropping every connection. The VBS window style 0 keeps the console hidden.
$py = Join-Path (Split-Path (Get-Command python.exe).Source) 'python.exe'
if (-not (Test-Path $py) -or $py -like '*WindowsApps*') { throw "real python.exe not found" }
$dist = Join-Path $root 'dist'
$vbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'portfolio-serve.vbs'
$cmd = '"' + $py + '" -m http.server 8787 --bind 127.0.0.1 --directory "' + $dist + '"'
$content = 'CreateObject("WScript.Shell").Run "' + $cmd.Replace('"', '""') + '", 0, False'
Set-Content -Path $vbs -Value $content -Encoding ASCII
Write-Output "Installed launcher: $vbs"
$busy = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
if ($busy) { Write-Output "Port 8787 already listening (pid $($busy.OwningProcess)); not starting a second copy." }
else { Start-Process -FilePath 'wscript.exe' -ArgumentList ('"' + $vbs + '"'); Write-Output "Started." }
