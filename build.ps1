$version = Invoke-Expression ('.\venv\Scripts\python.exe -c "from main import __version__;print(__version__)"')

New-Item -ErrorAction Ignore -ItemType Directory -Path release
Set-Location .\release
Invoke-Expression ("..\venv\Scripts\pyinstaller.exe ..\main.spec")

Write-Output  "build version: $version"

# crate release dir 
$releasedir = "exm_server_" + $version +"_windows"
New-Item -ItemType Directory -Path $releasedir

# move config file
Copy-Item -Force ..\config.example.ini .\$releasedir\config.ini
Copy-Item -Force ..\plugin.js .\$releasedir\plugin.js

# rename main.exe
$newname = "exm_server.exe"
Move-Item -Force .\dist\main.exe .\$newname

# move exe to run
Copy-Item -Force .\$newname ..\exm_server.exe

# pack release dir
Move-Item -Force .\$newname .\$releasedir
Compress-Archive -Force -Path .\$releasedir -DestinationPath .\$releasedir.zip

# clean up
Remove-Item -Recurse -Force .\$releasedir
Remove-Item -Recurse -Force .\dist