<#
.SYNOPSIS
    Convert one or more .docx files to .pdf via Word COM automation,
    reusing a single Word instance across the whole batch.

.DESCRIPTION
    Formalizes SKILL.md step 1a's inline PowerShell recipe into an actual
    checked-in script, instead of the agent retyping the same COM calls
    from prose each run. Confirms Word is installed before starting, and
    verifies each output PDF was actually created and is non-empty
    (SKILL.md's existing prose never verified conversion success).

.PARAMETER InputPaths
    One or more local .docx file paths to convert.

.PARAMETER OutputDir
    Directory to write the .pdf files into. Defaults to each input
    file's own directory. Output filename is the input filename with
    its extension swapped to .pdf.

.OUTPUTS
    Writes one JSON object per input file to stdout (one line each, for
    easy line-by-line consumption): {"input": "...", "output": "...",
    "ok": true} or {"input": "...", "error": "..."}.

.EXAMPLE
    ./convert_docx_to_pdf.ps1 -InputPaths "C:\docs\FO-00127 Rev 02-A.docx"
#>
param(
    [Parameter(Mandatory = $true)]
    [string[]]$InputPaths,

    [string]$OutputDir
)

$wordExePath = Get-ItemProperty `
    -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE" `
    -ErrorAction SilentlyContinue
if (-not $wordExePath) {
    Write-Output (@{ error = "Microsoft Word is not installed (WINWORD.EXE App Paths key not found)." } | ConvertTo-Json -Compress)
    exit 1
}

$wdFormatPDF = 17
$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    foreach ($inputPath in $InputPaths) {
        $resolvedInput = Resolve-Path -LiteralPath $inputPath -ErrorAction SilentlyContinue
        if (-not $resolvedInput) {
            Write-Output (@{ input = $inputPath; error = "File not found." } | ConvertTo-Json -Compress)
            continue
        }
        $inputFile = Get-Item -LiteralPath $resolvedInput
        $targetDir = if ($OutputDir) { $OutputDir } else { $inputFile.DirectoryName }
        $outputPath = Join-Path $targetDir ([System.IO.Path]::GetFileNameWithoutExtension($inputFile.Name) + ".pdf")

        try {
            $doc = $word.Documents.Open($inputFile.FullName, $false, $true)
            $doc.SaveAs([ref]$outputPath, [ref]$wdFormatPDF)
            $doc.Close($false)
        } catch {
            Write-Output (@{ input = $inputFile.FullName; error = $_.Exception.Message } | ConvertTo-Json -Compress)
            continue
        }

        if ((Test-Path -LiteralPath $outputPath) -and ((Get-Item -LiteralPath $outputPath).Length -gt 0)) {
            Write-Output (@{ input = $inputFile.FullName; output = $outputPath; ok = $true } | ConvertTo-Json -Compress)
        } else {
            Write-Output (@{ input = $inputFile.FullName; error = "SaveAs completed but output PDF is missing or empty." } | ConvertTo-Json -Compress)
        }
    }
} finally {
    $word.Quit()
}
