$version = Invoke-Expression ('.\venv\Scripts\python.exe -c "from main import __version__;print(__version__)"')

New-Item -ErrorAction Ignore -ItemType Directory -Path release
Set-Location .\release
Invoke-Expression ("..\venv\Scripts\pyinstaller.exe ..\main.spec")

Write-Output  "build version: $version"

# rename main.exe
$newname = "eimg_server.exe"
Move-Item -Force .\dist\main.exe .\$newname

# move exe to run
Move-Item -Force .\$newname ..\exm_server.exe

# clean up
Remove-Item -Force -Recurse .\dist

Write-Output "build complete"

Pause