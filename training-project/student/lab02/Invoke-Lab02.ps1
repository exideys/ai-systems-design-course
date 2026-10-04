param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Fixtures', 'Live', 'Import', 'Compare', 'Review', 'Approve', 'Apply', 'Refusal', 'Verify', 'Submission')]
    [string]$Step,
    [string]$Vault = (Join-Path $env:USERPROFILE 'OneDrive\ai-systems-learning-vault'),
    [ValidateSet('OpenRouter', 'AGY')]
    [string]$Adapter = 'OpenRouter',
    [string]$ModelId,
    [string]$StudentId = 'exideys',
    [string[]]$RunIds = @('live-primary-01', 'live-primary-02'),
    [string]$SelectedRun = 'live-primary-01'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath $Vault -PathType Container)) {
    throw "External vault not found: $Vault"
}
$reportDir = 'reports/lab02'
$proposalId = 'lab02-structured-output-' + $SelectedRun
$validation = "$reportDir/runs/$SelectedRun/validation-result.json"
$review = "$reportDir/semantic-review.yaml"

function Invoke-Learning {
    param([string[]]$CliArguments, [int[]]$AllowedExitCodes = @(0))
    # Native programs may report an expected refusal on stderr in PowerShell 5.1.
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & uv run learning-project @CliArguments
        $commandExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedPreference
    }
    if ($commandExit -notin $AllowedExitCodes) {
        throw "learning-project exited with code $commandExit. Stop and read its output."
    }
}

Write-Host ('Account: ' + [Environment]::UserName + '; GitHub: ' + $StudentId)
Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'
Write-Host ('Working directory: ' + $projectRoot)

switch ($Step) {
    'Fixtures' {
        Invoke-Learning -CliArguments @('lab02', 'check-fixtures', '--vault', $Vault)
    }
    'Live' {
        if ($RunIds.Count -ne 2 -or $RunIds[0] -eq $RunIds[1]) {
            throw 'Provide exactly two different run identifiers.'
        }
        if ($Adapter -eq 'AGY' -and [string]::IsNullOrWhiteSpace($ModelId)) {
            throw 'Choose an available model using agy models and pass -ModelId.'
        }
        foreach ($run in $RunIds) {
            if ((Test-Path "$reportDir/runs/$run/raw-response.txt") -or
                (Test-Path "$reportDir/runs/$run/run-metadata.json")) {
                throw "Run $run already has immutable evidence. Use Import or new run identifiers."
            }
            Invoke-Learning -CliArguments @('lab02', 'prepare', '--vault', $Vault,
                '--report-dir', $reportDir, '--run-id', $run)
        }
        if ($Adapter -eq 'OpenRouter') {
            # The secret never enters command arguments, a file, or a transcript.
            $previousKey = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'Process')
            $secureKey = Read-Host 'OpenRouter API key (hidden; never paste into chat)' -AsSecureString
            $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
            try {
                $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
            } finally {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
                $secureKey.Dispose()
                Remove-Variable keyPointer, secureKey
            }
            try {
                foreach ($run in $RunIds) {
                    Invoke-Learning -CliArguments @('lab02', 'run-openrouter', '--report-dir',
                        $reportDir, '--run-id', $run, '--by', $StudentId)
                }
            } finally {
                [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', $previousKey, 'Process')
                Remove-Variable previousKey
            }
        } else {
            foreach ($run in $RunIds) {
                Invoke-Learning -CliArguments @('lab02', 'run-agy', '--report-dir', $reportDir,
                    '--run-id', $run, '--model-id', $ModelId, '--by', $StudentId)
            }
        }
        Write-Host 'Two live calls completed. Next step: Import.'
    }
    'Import' {
        $validRuns = @()
        $invalidRuns = @()
        foreach ($run in $RunIds) {
            $id = 'lab02-structured-output-' + $run
            $proposal = Join-Path $Vault "proposals/$id.md"
            if (-not (Test-Path -LiteralPath $proposal)) {
                Invoke-Learning -CliArguments @('lab02', 'import', '--vault', $Vault,
                    '--report-dir', $reportDir, '--run-id', $run, '--evidence-kind', 'live')
            }
            $output = "$reportDir/runs/$run/validation-result.json"
            if (-not (Test-Path $output)) {
                Invoke-Learning -CliArguments @('lab02', 'validate', '--vault', $Vault,
                    '--report-dir', $reportDir, '--proposal-id', $id, '--output', $output) -AllowedExitCodes @(0, 1)
            }
            $result = Get-Content -LiteralPath $output -Raw -Encoding UTF8 | ConvertFrom-Json
            $actualHash = (Get-FileHash -LiteralPath $proposal -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($result.proposal_id -ne $id -or $result.proposal_sha256 -ne $actualHash) {
                throw "Validation for $run does not bind the current proposal. Do not overwrite evidence."
            }
            if (-not $result.valid) {
                $invalidRuns += $run
                Write-Warning "Candidate $run failed validation; evidence was preserved."
                foreach ($validationError in $result.errors) {
                    Write-Host ('  - ' + $validationError) -ForegroundColor Red
                }
                continue
            }
            $validRuns += $run
            Write-Host "Validation passed for $run."
        }
        if ($validRuns.Count -eq 0) {
            throw 'Neither candidate passed validation. Obtain a new response with a new run ID; keep existing evidence.'
        }
        Write-Host ('Valid run(s): ' + ($validRuns -join ', '))
        if ($invalidRuns.Count -gt 0) {
            Write-Host 'You can compare both live runs; review and approve only a validated candidate.'
            Write-Host ('Use -SelectedRun ' + $validRuns[0] + ' for Review, Approve, Apply, and Refusal.')
        }
    }
    'Compare' {
        Invoke-Learning -CliArguments @('lab02', 'compare-live', '--vault', $Vault,
            '--report-dir', $reportDir, '--run-id', $RunIds[0], $RunIds[1])
        Get-Content -LiteralPath "$reportDir/live-comparison.json" -Encoding UTF8
    }
    'Review' {
        & uv run python student/lab02/write_semantic_review.py --vault $Vault --report-dir $reportDir --run-id $SelectedRun --by $StudentId
        if ($LASTEXITCODE -ne 0) { throw 'Semantic review was not saved.' }
    }
    'Approve' {
        Write-Host 'Read the source, candidate, exact quotes, and your semantic review before approval.'
        $confirmation = Read-Host 'Type the complete proposal ID to record your human approval'
        if ($confirmation -cne $proposalId) { throw 'Approval cancelled: proposal ID does not match.' }
        Invoke-Learning -CliArguments @('lab02', 'decide', '--vault', $Vault,
            '--proposal-id', $proposalId, '--validation', $validation, '--review', $review,
            '--approve', '--by', $StudentId)
        Get-Content -LiteralPath $review -Encoding UTF8
        Get-Content -LiteralPath (Join-Path $Vault "decisions/$proposalId-decision.md") -Encoding UTF8
    }
    'Apply' {
        Invoke-Learning -CliArguments @('lab02', 'apply', '--vault', $Vault,
            '--proposal-id', $proposalId, '--validation', $validation, '--review', $review)
        Get-Content -LiteralPath (Join-Path $Vault 'concepts/structured-output.md') -Encoding UTF8
        Get-Content -LiteralPath (Join-Path $Vault "operations/$proposalId-apply.md") -Encoding UTF8
    }
    'Refusal' {
        $concept = Join-Path $Vault 'concepts/structured-output.md'
        $before = (Get-FileHash -LiteralPath $concept -Algorithm SHA256).Hash.ToLowerInvariant()
        $operationsBefore = @(Get-ChildItem -LiteralPath (Join-Path $Vault 'operations') -Filter 'lab02-structured-output-*-apply.md' -File)
        $ErrorActionPreference = 'Continue'
        try {
            & uv run learning-project lab02 apply --vault $Vault --proposal-id $proposalId --validation $validation --review $review
            $refusalExit = $LASTEXITCODE
        } finally { $ErrorActionPreference = 'Stop' }
        $after = (Get-FileHash -LiteralPath $concept -Algorithm SHA256).Hash.ToLowerInvariant()
        $operationsAfter = @(Get-ChildItem -LiteralPath (Join-Path $Vault 'operations') -Filter 'lab02-structured-output-*-apply.md' -File)
        Write-Host "Refusal exit: $refusalExit"
        Write-Host "SHA256 before: $before"
        Write-Host "SHA256 after:  $after"
        Write-Host ('Successful Lab02 operations: ' + $operationsAfter.Count)
        if ($refusalExit -ne 1 -or $before -cne $after -or
            $operationsBefore.Count -ne 1 -or $operationsAfter.Count -ne 1) {
            throw 'Repeat-apply refusal did not meet the laboratory contract.'
        }
        Write-Host 'Refused; accepted bytes unchanged; exactly one successful operation.'
    }
    'Verify' {
        Invoke-Learning -CliArguments @('lab02', 'verify', '--vault', $Vault, '--report-dir', $reportDir)
        Write-Host 'status: passed; exit: 0'
    }
    'Submission' {
        $result = Get-Content -LiteralPath "$reportDir/verification-report.json" -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($result.status -ne 'passed') { throw 'Submission requires the final passed verification.' }
        foreach ($artifact in $result.artifacts.PSObject.Properties) {
            if ($artifact.Name.StartsWith('report/')) {
                $file = Join-Path $reportDir $artifact.Name.Substring(7)
            } elseif ($artifact.Name.StartsWith('vault/')) {
                $file = Join-Path $Vault $artifact.Name.Substring(6)
            } else { throw ('Unknown artifact location: ' + $artifact.Name) }
            $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($hash -cne $artifact.Value) {
                throw "Artifact changed after verification: $file. Verify again before packaging."
            }
        }
        Invoke-Learning -CliArguments @('prepare-report', "$reportDir/REPORT.md")
        $embedded = Get-Content -LiteralPath "$reportDir/submission/REPORT.md" -Raw -Encoding UTF8
        if ([regex]::Matches($embedded, 'data:image/').Count -ne 6) {
            throw 'Expected exactly six embedded screenshots.'
        }
        Write-Host 'Attach these four individual files in Teams:'
        @('submission/REPORT.md', 'verification-report.json', 'live-comparison.json', 'semantic-review.yaml') |
            ForEach-Object { Write-Host (Join-Path $projectRoot "$reportDir/$_") }
    }
}
