$ErrorActionPreference = 'Stop'
$taskRenderRoot = Join-Path $PSScriptRoot 'outputs/web-room-v160'
$taskMediaRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'public/room/v160'
New-Item -ItemType Directory -Force -Path $taskMediaRoot | Out-Null
foreach ($taskName in @('books-still','books-background')) {
    & ffmpeg -v error -y -i (Join-Path $taskRenderRoot "$taskName.png") -c:v libwebp -lossless 1 (Join-Path $taskMediaRoot "$taskName.webp")
    if ($LASTEXITCODE -ne 0) { throw "Still encoding failed: $taskName" }
}
if ($args -contains '--plates-only') { exit 0 }
foreach ($taskName in @('books-in','books-out','shelf-1-0','shelf-0-1')) {
    $taskCount = if ($taskName.StartsWith('books-')) { 73 } else { 37 }
    for ($taskFrame=0; $taskFrame -lt $taskCount; $taskFrame++) {
        $taskPath = Join-Path (Join-Path $taskRenderRoot $taskName) ('{0:D4}.png' -f $taskFrame)
        if (!(Test-Path -LiteralPath $taskPath)) { throw "Missing render: $taskPath" }
    }
    & ffmpeg -v error -y -framerate 24 -i (Join-Path $taskRenderRoot "$taskName/%04d.png") -frames:v $taskCount -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $taskMediaRoot "$taskName.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Video encoding failed: $taskName" }
    Write-Output "V160_ENCODED $taskName"
}
