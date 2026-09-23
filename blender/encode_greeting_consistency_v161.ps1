$ErrorActionPreference = 'Stop'
$renderRoot = Join-Path $PSScriptRoot 'outputs/web-room-v161'
$mediaRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'public/room/v161'
New-Item -ItemType Directory -Force -Path $mediaRoot | Out-Null
foreach ($clip in @('idle','monitor-in','monitor-out','diploma-in','diploma-out')) {
    $count = if ($clip -eq 'idle') { 240 } elseif ($clip -like 'monitor-*') { 121 } else { 73 }
    for ($frame=0; $frame -lt $count; $frame++) {
        if (!(Test-Path -LiteralPath (Join-Path $renderRoot ("$clip/{0:D4}.png" -f $frame)))) { throw "Missing $clip frame $frame" }
    }
    & ffmpeg -v error -y -framerate 24 -i (Join-Path $renderRoot "$clip/%04d.png") -frames:v $count -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $mediaRoot "$clip.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $clip" }
}
& ffmpeg -v error -y -i (Join-Path $renderRoot 'greeting-probe/0000.png') -quality 95 (Join-Path $mediaRoot 'greeting.webp')
if ($LASTEXITCODE -ne 0) { throw 'Greeting encoding failed' }
& ffmpeg -v error -y -i (Join-Path $renderRoot 'diploma-in/0072.png') -quality 95 (Join-Path $mediaRoot 'diploma.webp')
if ($LASTEXITCODE -ne 0) { throw 'Diploma encoding failed' }
