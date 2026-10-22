$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$operatorName = Read-Host 'Operator name (who actually starts this run)'
if ([string]::IsNullOrWhiteSpace($operatorName)) { throw 'Operator name is required' }
python lab.py doctor
if ($LASTEXITCODE -ne 0) { throw 'Docker is not ready' }
python lab.py build
if ($LASTEXITCODE -ne 0) { throw 'Build failed; see build.log' }
$consoleName = 'evidence\pilot-console-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '.log'
$collectedOutput = @()
python lab.py collect --phase pilot --rounds 2 --operator $operatorName | Tee-Object -Variable collectedOutput | Tee-Object -FilePath $consoleName -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw 'Collection incomplete: preserve raw files and inspect errors' }
$runLine = $collectedOutput | Where-Object { $_ -like 'RUN DIRECTORY: *' } | Select-Object -Last 1
if (-not $runLine) { throw 'Run path not found in output' }
$runPath = $runLine.Substring('RUN DIRECTORY: '.Length).Trim()
python lab.py analyze $runPath
if ($LASTEXITCODE -ne 0) { throw 'Analysis failed' }
Write-Host "Finished. Results: $runPath\processed\RESULTS.md"
