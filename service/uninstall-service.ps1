# Remove the Startup launcher and stop the loopback server on 8787 if it is our pythonw http.server.
$vbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'portfolio-serve.vbs'
if (Test-Path $vbs) { Remove-Item $vbs -Confirm:$false; Write-Output "Removed $vbs" }
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*http.server 8787*--bind 127.0.0.1*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Confirm:$false; Write-Output "Stopped pid $($_.ProcessId)" }
