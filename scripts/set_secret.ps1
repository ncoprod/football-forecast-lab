param(
    [ValidateSet("THE_ODDS_API_KEY", "API_FOOTBALL_KEY")]
    [string]$Name = "THE_ODDS_API_KEY"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$EnvPath = Join-Path $RepoRoot ".env"
$ExamplePath = Join-Path $RepoRoot ".env.example"

if (-not (Test-Path -LiteralPath $EnvPath)) {
    if (Test-Path -LiteralPath $ExamplePath) {
        Copy-Item -LiteralPath $ExamplePath -Destination $EnvPath
    }
    else {
        New-Item -ItemType File -Path $EnvPath | Out-Null
    }
}

$SecureValue = Read-Host "Enter $Name" -AsSecureString
$Bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
try {
    $PlainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Bstr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
}

if ([string]::IsNullOrWhiteSpace($PlainValue)) {
    throw "$Name cannot be empty."
}
if ($PlainValue.Contains("`n") -or $PlainValue.Contains("`r")) {
    throw "$Name cannot contain a newline."
}

$Lines = @()
if (Test-Path -LiteralPath $EnvPath) {
    $Lines = @(Get-Content -LiteralPath $EnvPath)
}

$Updated = $false
$NextLines = foreach ($Line in $Lines) {
    if ($Line -match "^\s*$([regex]::Escape($Name))\s*=") {
        "$Name=$PlainValue"
        $Updated = $true
    }
    else {
        $Line
    }
}

if (-not $Updated) {
    $NextLines += "$Name=$PlainValue"
}

Set-Content -LiteralPath $EnvPath -Value $NextLines -Encoding UTF8
Write-Host "$Name saved to .env. The value was not printed and .env is ignored by Git."
