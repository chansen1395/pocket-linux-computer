# Pocket Linux Computer flash. Runs elevated (via 2-flash.cmd). Writes the Raspberry Pi OS image plus the cloud-init
# first-boot files to the one USB disk of roughly 64 GB, and refuses anything else.
param([switch]$NoPause)
$ErrorActionPreference = 'Continue'
function Pause-Unless { param($m) if (-not $NoPause) { Read-Host $m } }
$kit    = Split-Path -Parent $MyInvocation.MyCommand.Path
$imager = 'C:\Program Files\Raspberry Pi Ltd\Imager\rpi-imager.exe'
$image  = Get-ChildItem "$kit\*.img.xz" | Select-Object -First 1
$log    = "$kit\flash.log"

function Say($m) { $m | Tee-Object -FilePath $log -Append }
"flash start $(Get-Date -Format s)" | Out-File $log -Encoding utf8

if (-not (Test-Path $imager)) { Say "Raspberry Pi Imager not found at $imager"; Pause-Unless 'Enter to close'; exit 3 }
if (-not $image) { Say "no .img.xz in $kit"; Pause-Unless 'Enter to close'; exit 3 }
foreach ($f in @("$kit\user-data", "$kit\network-config")) { if (-not (Test-Path $f)) { Say "missing $f"; Pause-Unless 'Enter to close'; exit 3 } }

$cands = @(Get-Disk | Where-Object { $_.BusType -in @('USB','SD','MMC') -and $_.Size -gt 50GB -and $_.Size -lt 70GB })
if ($cands.Count -ne 1) {
  Say "REFUSED: expected exactly one USB/SD disk of ~64 GB, found $($cands.Count). Disks:"
  Get-Disk | Format-Table -AutoSize Number, FriendlyName, BusType, @{n='SizeGB';e={[math]::Round($_.Size/1GB,1)}} | Out-String | Tee-Object -FilePath $log -Append
  Pause-Unless 'Enter to close'; exit 2
}
$d = $cands[0]
$target = "\\.\PhysicalDrive$($d.Number)"
Say "target: disk #$($d.Number) '$($d.FriendlyName)' $([math]::Round($d.Size/1GB,1)) GB -> $target"
Say "image:  $($image.Name)"
Say "writing and verifying; this takes 5-10 minutes..."

& $imager --cli --debug --cloudinit-userdata "$kit\user-data" --cloudinit-networkconfig "$kit\network-config" $image.FullName $target 2>&1 | Tee-Object -FilePath $log -Append
$code = $LASTEXITCODE
Say "imager exit: $code  at $(Get-Date -Format s)"
if ($code -eq 0) {
  Say "DONE. Unplug the Pi from the PC, connect its power supply, wait 3 minutes. It joins the Wi-Fi network from your network-config."
  $boot = Get-Volume | Where-Object { $_.FileSystemLabel -match 'boot' -and $_.DriveType -eq 'Removable' } | Select-Object -First 1
  if ($boot) { Say "boot partition mounted as $($boot.DriveLetter): -> user-data present: $(Test-Path ($boot.DriveLetter + ':\user-data'))" }
} else {
  Say "FAILED. If the message mentions unknown options, run: rpi-imager --cli --help"
}
Pause-Unless 'Enter to close'
exit $code
