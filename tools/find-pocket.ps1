# Finds the device on the local network and prints its address.
# Tries mDNS (pocket.local) first, then a ping sweep of the PC's /24 looking for Raspberry Pi MAC
# prefixes, skipping any addresses given in -Exclude (for example another Pi on the LAN).
#   powershell -File tools/find-pocket.ps1 -Exclude 192.0.2.10
param([string[]]$Exclude = @(), [string]$Name = 'pocket.local')

$ouis = '2c-cf-67|d8-3a-dd|e4-5f-01|dc-a6-32|b8-27-eb|28-cd-c1|88-a2-9e'

$r = ping -n 1 -w 1000 $Name 2>&1 | Select-String 'Reply from ([0-9.]+)'
if ($r) { Write-Output $r.Matches[0].Groups[1].Value; exit 0 }

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixLength -ge 16 } | Select-Object -First 1).IPAddress
if (-not $ip) { Write-Error 'no LAN address on this PC'; exit 2 }
$s = ($ip -split '\.')[0..2] -join '.'
$tasks = foreach ($i in 1..254) { $a = "$s.$i"; if ($Exclude -notcontains $a) { (New-Object System.Net.NetworkInformation.Ping).SendPingAsync($a, 600) } }
try { [System.Threading.Tasks.Task]::WaitAll([System.Threading.Tasks.Task[]]$tasks) } catch {}
$hits = arp -a | Select-String $ouis | ForEach-Object { ($_.Line.Trim() -split '\s+')[0] } | Where-Object { $Exclude -notcontains $_ }
if ($hits) { $hits | Select-Object -First 1; exit 0 }
Write-Error 'Pocket device not found'; exit 1
