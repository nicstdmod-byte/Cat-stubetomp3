# Cat'sTube2Mp3 helper installer for Windows.
# Installs into %LOCALAPPDATA%\CatsTube2Mp3 and registers the helper with Firefox, Chrome and Edge.
# No admin rights needed. Easiest way to run: double-click install.bat.
param([switch]$UpdateFfmpeg)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # makes Invoke-WebRequest much faster
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$HostName   = 'catstube2mp3.helper'
$FirefoxId  = 'catstube2mp3@catstube2mp3.local'
$ChromeId   = 'ohhfjoepjlifkbodjampofpmdbplgccg'

# Official portable ("embeddable") Python from python.org; python.exe inside is signed by the Python Software Foundation.
$PythonVersion = '3.14.10'
$PythonSha256  = '90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159'
$PythonUrl     = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$GetPipUrl     = 'https://bootstrap.pypa.io/get-pip.py'
# ffmpeg builds made for yt-dlp; checked against the checksum file published with the same release.
$FfmpegBase    = 'https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest'
$FfmpegZip     = 'ffmpeg-master-latest-win64-gpl.zip'

$Repo   = Split-Path -Parent $PSScriptRoot
$App    = Join-Path $env:LOCALAPPDATA 'CatsTube2Mp3'
$PyDir  = Join-Path $App 'python'
$Python = Join-Path $PyDir 'python.exe'
$Temp   = Join-Path $env:TEMP 'CatsTube2Mp3-install'

function Say($text)  { Write-Host "==> $text" -ForegroundColor Yellow }
function Fail($text) { Write-Host "Error: $text" -ForegroundColor Red; exit 1 }

function Download($url, $file) {
    Invoke-WebRequest -Uri $url -OutFile $file -UseBasicParsing
}

function Check-Hash($file, $expected) {
    $actual = (Get-FileHash -Algorithm SHA256 $file).Hash.ToLower()
    if ($actual -ne $expected.ToLower()) {
        Fail "Download check failed for $(Split-Path -Leaf $file) (got $actual). Try again later."
    }
}

function Test-Command([scriptblock]$command) {
    # Windows PowerShell 5.1 turns redirected stderr into terminating errors under 'Stop', so relax it here.
    $ErrorActionPreference = 'Continue'
    & $command *> $null
    return $LASTEXITCODE -eq 0
}

function Write-Text($path, $text) {
    # UTF-8 without BOM; browsers can fail to read JSON files that start with a BOM.
    [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false))
}

New-Item -ItemType Directory -Force -Path $App, $Temp | Out-Null

# ---------------------------------------------------------------- Python
$pythonReady = (Test-Path $Python) -and (Test-Command { & $Python -c "import platform, sys; sys.exit(platform.python_version() != '$PythonVersion')" })
if (-not $pythonReady) {
    Say "Downloading Python $PythonVersion from python.org"
    $zip = Join-Path $Temp 'python.zip'
    Download $PythonUrl $zip
    Check-Hash $zip $PythonSha256
    if (Test-Path $PyDir) { Remove-Item -Recurse -Force $PyDir }
    Expand-Archive -Path $zip -DestinationPath $PyDir
}

# The embeddable Python ignores site-packages until "import site" is enabled in its ._pth file.
$tag = ($PythonVersion -split '\.')[0..1] -join ''
Write-Text (Join-Path $PyDir "python$tag._pth") "python$tag.zip`r`n.`r`n..\helper`r`nimport site`r`n"

# ---------------------------------------------------------------- pip, yt-dlp, deno
if (-not (Test-Command { & $Python -m pip --version })) {
    Say 'Setting up pip'
    $getPip = Join-Path $Temp 'get-pip.py'
    Download $GetPipUrl $getPip
    & $Python $getPip --no-warn-script-location --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Fail 'Could not set up pip.' }
}

Say 'Copying helper files'
New-Item -ItemType Directory -Force -Path (Join-Path $App 'helper') | Out-Null
Copy-Item -Force (Join-Path $Repo 'helper\*.py'), (Join-Path $Repo 'helper\requirements.txt') (Join-Path $App 'helper')

Say 'Installing yt-dlp and deno (this can take a minute)'
& $Python -m pip install --upgrade --quiet --no-warn-script-location --disable-pip-version-check -r (Join-Path $App 'helper\requirements.txt')
if ($LASTEXITCODE -ne 0) { Fail 'Could not install yt-dlp.' }

# ---------------------------------------------------------------- ffmpeg
$ffmpegExe = Join-Path $App 'ffmpeg\bin\ffmpeg.exe'
if ($UpdateFfmpeg -or -not (Test-Path $ffmpegExe)) {
    Say 'Downloading ffmpeg'
    $zip = Join-Path $Temp $FfmpegZip
    $sums = Join-Path $Temp 'checksums.sha256'
    Download "$FfmpegBase/$FfmpegZip" $zip
    Download "$FfmpegBase/checksums.sha256" $sums
    $line = Select-String -Path $sums -Pattern ([regex]::Escape($FfmpegZip)) | Select-Object -First 1
    if (-not $line) { Fail 'Could not find the ffmpeg checksum.' }
    Check-Hash $zip (($line.Line -split '\s+')[0])
    $unpacked = Join-Path $Temp 'ffmpeg'
    if (Test-Path $unpacked) { Remove-Item -Recurse -Force $unpacked }
    Expand-Archive -Path $zip -DestinationPath $unpacked
    $bin = Get-ChildItem -Path $unpacked -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1
    if (-not $bin) { Fail 'ffmpeg.exe not found in the download.' }
    $target = Join-Path $App 'ffmpeg'
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Move-Item $bin.Directory.FullName (Join-Path $target 'bin')
}

# ---------------------------------------------------------------- browser registration
Say 'Registering with browsers'
$launcher = Join-Path $App 'catstube2mp3-host.bat'
Write-Text $launcher "@echo off`r`n`"%~dp0python\python.exe`" `"%~dp0helper\catstube2mp3_host.py`" %*`r`n"

$firefoxManifest = Join-Path $App "$HostName.firefox.json"
$chromeManifest  = Join-Path $App "$HostName.chrome.json"
Write-Text $firefoxManifest (@{
    name = $HostName; description = "Cat'sTube2Mp3 helper"; path = $launcher; type = 'stdio'
    allowed_extensions = @($FirefoxId)
} | ConvertTo-Json)
Write-Text $chromeManifest (@{
    name = $HostName; description = "Cat'sTube2Mp3 helper"; path = $launcher; type = 'stdio'
    allowed_origins = @("chrome-extension://$ChromeId/")
} | ConvertTo-Json)

$registrations = @{
    'HKCU:\Software\Mozilla\NativeMessagingHosts'          = $firefoxManifest
    'HKCU:\Software\Google\Chrome\NativeMessagingHosts'    = $chromeManifest
    'HKCU:\Software\Chromium\NativeMessagingHosts'         = $chromeManifest
    'HKCU:\Software\Microsoft\Edge\NativeMessagingHosts'   = $chromeManifest
}
foreach ($entry in $registrations.GetEnumerator()) {
    $key = Join-Path $entry.Key $HostName
    New-Item -Path $key -Force | Out-Null
    Set-ItemProperty -Path $key -Name '(default)' -Value $entry.Value
    Write-Host "    $key"
}

# ---------------------------------------------------------------- self test
Say 'Testing the helper'
$test = @'
import json, struct, subprocess, sys
data = json.dumps({"cmd": "ping"}).encode()
out = subprocess.run([sys.argv[1]], input=struct.pack("=I", len(data)) + data, capture_output=True, timeout=60).stdout
reply = json.loads(out[4:])
if not reply.get("ok"):
    sys.exit("Helper test failed: " + str(reply))
print(f"    helper {reply['helper']}, yt-dlp {reply['ytdlp']}, ffmpeg: {'yes' if reply['ffmpeg'] else 'NO'}, "
      f"JavaScript runtime: {reply['jsRuntime'] or 'NONE'}")
'@
$testFile = Join-Path $Temp 'selftest.py'
Write-Text $testFile $test
& $Python $testFile $launcher
if ($LASTEXITCODE -ne 0) { Fail 'The helper test failed. See the message above.' }

Remove-Item -Recurse -Force $Temp -ErrorAction SilentlyContinue
Say "Done! Restart your browser, then click the Cat'sTube2Mp3 icon on a YouTube playlist."
