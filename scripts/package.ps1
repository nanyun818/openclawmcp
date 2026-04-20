param(
    [string]$OutputDir = "D:\Codex\openclaw-lab-agent\packages",
    [string]$PackageName = "",
    [switch]$IncludeTests
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if ([string]::IsNullOrWhiteSpace($PackageName)) {
    $PackageName = "openclaw-lab-agent-$Timestamp.zip"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$PackagePath = Join-Path $OutputDir $PackageName
$HashPath = "$PackagePath.sha256"

if (Test-Path -LiteralPath $PackagePath) {
    throw "Package already exists: $PackagePath"
}

$RootPrefix = $ProjectRoot.Path.TrimEnd("\") + "\"

$ExcludedDirs = @(
    ".git",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "runs",
    "packages"
)

$ExcludedFiles = @(
    ".env"
)

$ExcludedExtensions = @(
    ".pyc",
    ".pyo",
    ".log"
)

if (-not $IncludeTests) {
    $ExcludedDirs += "tests"
}

function Test-IsExcluded {
    param([System.IO.FileInfo]$File)

    $Relative = $File.FullName.Substring($RootPrefix.Length)
    $Parts = $Relative -split "[\\/]+"

    foreach ($Part in $Parts) {
        if ($ExcludedDirs -contains $Part) {
            return $true
        }
    }

    if ($ExcludedFiles -contains $File.Name) {
        return $true
    }

    if ($ExcludedExtensions -contains $File.Extension) {
        return $true
    }

    return $false
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$Zip = [System.IO.Compression.ZipFile]::Open($PackagePath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $Files = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File | Where-Object { -not (Test-IsExcluded $_) }

    foreach ($File in $Files) {
        $Relative = $File.FullName.Substring($RootPrefix.Length).Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($Zip, $File.FullName, $Relative) | Out-Null
    }
}
finally {
    $Zip.Dispose()
}

$Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath
"$($Hash.Hash.ToLower())  $PackageName" | Set-Content -LiteralPath $HashPath -Encoding ascii

[PSCustomObject]@{
    package = $PackagePath
    sha256 = $HashPath
    include_tests = [bool]$IncludeTests
}
