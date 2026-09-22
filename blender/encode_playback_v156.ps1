$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$renderRoot=Join-Path $PSScriptRoot 'outputs/web-room-v156'
$mediaRoot=Join-Path $projectRoot 'public/room/v156'
New-Item -ItemType Directory -Force -Path $mediaRoot | Out-Null
foreach($name in @('vinyl-still','vinyl-background')){
  & ffmpeg -v error -y -i (Join-Path $renderRoot "$name.png") -c:v libwebp -lossless 1 (Join-Path $mediaRoot "$name.webp")
  if($LASTEXITCODE -ne 0){throw "Failed to encode $name"}
}
foreach($name in @('playback','return')){
  & ffmpeg -v error -y -framerate 24 -i (Join-Path $renderRoot "$name/%04d.png") -c:v libx264 -crf 16 -preset slow -threads 3 -pix_fmt yuv420p -movflags +faststart (Join-Path $mediaRoot "$name-background.mp4")
  if($LASTEXITCODE -ne 0){throw "Failed to encode $name"}
}
& ffmpeg -v error -y -i (Join-Path $renderRoot 'playback/0137.png') -c:v libwebp -lossless 1 (Join-Path $mediaRoot 'playback-end.webp')
if($LASTEXITCODE -ne 0){throw 'Failed to encode playback endpoint'}
