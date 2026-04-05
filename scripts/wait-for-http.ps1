param(
  [Parameter(Mandatory = $true)]
  [string]$Url,
  [int]$TimeoutSeconds = 60,
  [int]$DelaySeconds = 2
)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $deadline) {
  try {
    $response = Invoke-WebRequest -Uri $Url
    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
      Write-Host "Reachable: $Url"
      exit 0
    }
  } catch {
    Start-Sleep -Seconds $DelaySeconds
  }
}

Write-Error "Timed out waiting for $Url"
exit 1

