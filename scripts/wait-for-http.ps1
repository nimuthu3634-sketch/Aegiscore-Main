param(
  [Parameter(Mandatory = $true)]
  [string]$Url,
  [int]$TimeoutSeconds = 60,
  [int]$DelaySeconds = 2
)

# This script waits until a web endpoint becomes reachable.
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $deadline) {
  try {
    $response = Invoke-WebRequest -Uri $Url
    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
      Write-Host "Reachable: $Url"
      exit 0
    }
  } catch {
    # If the request fails, wait briefly and try again.
    Start-Sleep -Seconds $DelaySeconds
  }
}

Write-Error "Timed out waiting for $Url"
exit 1
