$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VendorDir = Join-Path $ProjectRoot "vendor\ffmpeg"
$DistDir = Join-Path $ProjectRoot "distr"
$WorkDir = Join-Path $ProjectRoot "build\windows"
$SpecDir = Join-Path $WorkDir "spec"

New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
New-Item -ItemType Directory -Force -Path $SpecDir | Out-Null

function Resolve-ToolPath([string]$ToolName) {
    $ResolvedPaths = @()
    $WhereOutput = & where.exe $ToolName 2>$null
    if ($WhereOutput) {
        $ResolvedPaths += ($WhereOutput -split "`r?`n" | Where-Object { $_ })
    }

    $Command = Get-Command $ToolName -ErrorAction Stop
    if ($Command.Source) {
        $ResolvedPaths += $Command.Source
    }

    $ChocolateyInstall = $env:ChocolateyInstall
    if ($ChocolateyInstall) {
        $ResolvedPaths += Join-Path $ChocolateyInstall "lib\ffmpeg\tools\ffmpeg\bin\$ToolName.exe"
        $ResolvedPaths += Join-Path $ChocolateyInstall "lib\ffmpeg-full\tools\ffmpeg\bin\$ToolName.exe"
    }

    $SourcePath = $ResolvedPaths |
        Where-Object { $_ -and (Test-Path $_) } |
        Where-Object { $_ -notmatch '\\chocolatey\\bin\\' } |
        Select-Object -First 1

    if (-not $SourcePath) {
        throw "Could not resolve real binary for $ToolName"
    }

    return (Resolve-Path $SourcePath).Path
}

function Copy-ToolBundleToVendor([string]$ToolName) {
    $SourcePath = Resolve-ToolPath $ToolName
    $SourceDir = Split-Path $SourcePath -Parent
    $BundleFiles = @($SourcePath)
    $BundleFiles += Get-ChildItem -Path $SourceDir -File -Filter "*.dll" | Select-Object -ExpandProperty FullName

    foreach ($FilePath in ($BundleFiles | Sort-Object -Unique)) {
        $TargetPath = Join-Path $VendorDir ([System.IO.Path]::GetFileName($FilePath))
        Copy-Item $FilePath $TargetPath -Force
    }
}

# Bundle ffmpeg and its runtime DLLs. ffprobe is not required for extraction,
# and excluding it keeps the single-file build under GitHub's 100 MB limit.
Copy-ToolBundleToVendor "ffmpeg"

$IconPng = Join-Path $ProjectRoot "assets\icon.png"
$IconIco = Join-Path $ProjectRoot "assets\icon.ico"
$MainScript = Join-Path $ProjectRoot "main.py"

$PyInstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "YTMusic Smart Downloader",
    "--icon", $IconIco,
    "--paths", $ProjectRoot,
    "--distpath", $DistDir,
    "--workpath", $WorkDir,
    "--specpath", $SpecDir,
    "--add-data", "${IconPng};assets",
    "--add-data", "${IconIco};assets",
    "--collect-all", "customtkinter",
    "--collect-all", "yt_dlp",
    "--collect-all", "PIL",
    "--collect-all", "mutagen",
    $MainScript
)

foreach ($VendorFile in Get-ChildItem -Path $VendorDir -File | Sort-Object Name) {
    $PyInstallerArgs += @("--add-binary", "$($VendorFile.FullName);.")
}

python -m PyInstaller @PyInstallerArgs

Write-Host ""
Write-Host "Windows build ready:"
Write-Host "  $(Join-Path $DistDir 'YTMusic Smart Downloader.exe')"
