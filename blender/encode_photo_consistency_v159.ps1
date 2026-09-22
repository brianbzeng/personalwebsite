$ErrorActionPreference = 'Stop'
$taskRenderRoot = Join-Path $PSScriptRoot 'outputs/web-room-v159'
$taskMediaRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'public/room/v159'
New-Item -ItemType Directory -Force -Path $taskMediaRoot | Out-Null
foreach ($taskName in @('photos-still','photos-background')) {
    & ffmpeg -v error -y -i (Join-Path $taskRenderRoot "$taskName.png") -c:v libwebp -lossless 1 (Join-Path $taskMediaRoot "$taskName.webp")
    if ($LASTEXITCODE -ne 0) { throw "Still encoding failed: $taskName" }
}
if ($args -contains '--plates-only') { exit 0 }
foreach ($taskName in @('photos-in','photos-out','shelf-1-2','shelf-2-1')) {
    $taskCount = if ($taskName.StartsWith('photos-')) { 91 } else { 37 }
    $taskFps = if ($taskName.StartsWith('photos-')) { 30 } else { 24 }
    for ($taskFrame=0; $taskFrame -lt $taskCount; $taskFrame++) {
        $taskPath = Join-Path (Join-Path $taskRenderRoot $taskName) ('{0:D4}.png' -f $taskFrame)
        if (!(Test-Path -LiteralPath $taskPath)) { throw "Missing render: $taskPath" }
    }
    & ffmpeg -v error -y -framerate $taskFps -i (Join-Path $taskRenderRoot "$taskName/%04d.png") -frames:v $taskCount -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $taskMediaRoot "$taskName.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Video encoding failed: $taskName" }
    Write-Output "V159_ENCODED $taskName"
}
