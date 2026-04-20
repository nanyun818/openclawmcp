param(
    [string]$HostName = "124.222.101.170",
    [string]$User = "ubuntu",
    [string]$RemoteRoot = "/data/openclaw-lab-agent",
    [string]$PackagePath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    $Latest = Get-ChildItem "D:\Codex\openclaw-lab-agent\packages\openclaw-lab-agent-*.zip" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $Latest) {
        throw "No package found. Run .\scripts\package.ps1 first."
    }

    $PackagePath = $Latest.FullName
}

$PackagePath = (Resolve-Path $PackagePath).Path
$PackageName = Split-Path $PackagePath -Leaf
$RemoteUpload = "$RemoteRoot/uploads/$PackageName"

Write-Host "Package: $PackagePath"
Write-Host "Server:  $User@$HostName"
Write-Host "Target:  $RemoteRoot"
Write-Host ""
Write-Host "The SSH client may ask for the server password and sudo password."
Write-Host "This script does not store passwords and does not delete server files."
Write-Host ""

$Prepare = "sudo mkdir -p '$RemoteRoot/uploads' '$RemoteRoot/app' && sudo chown -R '${User}:${User}' '$RemoteRoot'"
ssh -t "$User@$HostName" $Prepare

scp $PackagePath "${User}@${HostName}:$RemoteUpload"

$Extract = "python3 -m zipfile -e '$RemoteUpload' '$RemoteRoot/app' && find '$RemoteRoot/app' -maxdepth 2 -type f | sort | head -50"
ssh "$User@$HostName" $Extract

Write-Host ""
Write-Host "Upload complete."
Write-Host "Remote package: $RemoteUpload"
Write-Host "Remote app:     $RemoteRoot/app"
