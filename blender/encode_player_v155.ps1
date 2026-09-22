$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$renderRoot = Join-Path $PSScriptRoot 'outputs/web-room-v155'
$mediaRoot = Join-Path $projectRoot 'public/room/v155'
New-Item -ItemType Directory -Force -Path $mediaRoot | Out-Null
foreach ($name in @('vinyl-still','vinyl-background')) {
  & ffmpeg -v error -y -i (Join-Path $renderRoot "$name/0000.png") -c:v libwebp -lossless 1 (Join-Path $mediaRoot "$name.webp")
  if ($LASTEXITCODE -ne 0) { throw "Failed to encode $name" }
}
if ($args -contains '--plates-only') { exit 0 }
foreach ($name in @('vinyl-in','vinyl-out','shelf-1-0','shelf-0-1','shelf-1-2','shelf-2-1')) {
  & ffmpeg -v error -y -framerate 24 -i (Join-Path $renderRoot "$name/%04d.png") -c:v libx264 -crf 18 -preset slow -threads 3 -pix_fmt yuv420p -movflags +faststart (Join-Path $mediaRoot "$name.mp4")
  if ($LASTEXITCODE -ne 0) { throw "Failed to encode $name" }
}
