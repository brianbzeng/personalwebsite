param([ValidateSet('monitor-in','monitor-out')][string[]]$Clips = @('monitor-in','monitor-out'))
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$output = Join-Path $project 'public/room/v133'
New-Item -ItemType Directory -Force -Path $output | Out-Null
foreach ($clip in $Clips) {
    $frames = Join-Path $PSScriptRoot "outputs/web-room-v133/$clip"
    if (@(Get-ChildItem -LiteralPath $frames -Filter '*.png').Count -ne 121) { throw "Incomplete $clip frames" }
    & ffmpeg -hide_banner -loglevel error -n -framerate 24 -i "$frames/%04d.png" -frames:v 121 -c:v libx264 -threads 4 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an "$output/$clip.mp4"
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $clip" }
}
