# Removes the Cat'sTube2Mp3 helper. Your downloaded MP3 files are not touched.
$ErrorActionPreference = 'Continue'
$HostName = 'catstube2mp3.helper'

foreach ($base in 'HKCU:\Software\Mozilla\NativeMessagingHosts',
                  'HKCU:\Software\Google\Chrome\NativeMessagingHosts',
                  'HKCU:\Software\Chromium\NativeMessagingHosts',
                  'HKCU:\Software\Microsoft\Edge\NativeMessagingHosts') {
    Remove-Item -Path (Join-Path $base $HostName) -Force -ErrorAction SilentlyContinue
}
Remove-Item -Recurse -Force (Join-Path $env:LOCALAPPDATA 'CatsTube2Mp3') -ErrorAction SilentlyContinue
Write-Host "Cat'sTube2Mp3 helper removed. Remove the browser extension from the browser's add-ons page."
