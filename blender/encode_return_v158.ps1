$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$renderRoot=Join-Path $PSScriptRoot 'outputs/web-room-v158/return'
$mediaRoot=Join-Path $projectRoot 'public/room/v158'
New-Item -ItemType Directory -Force -Path $mediaRoot | Out-Null
& ffmpeg -v error -y -framerate 24 -i (Join-Path $renderRoot '%04d.png') -c:v libx264 -crf 16 -preset slow -threads 3 -pix_fmt yuv420p -movflags +faststart (Join-Path $mediaRoot 'return-background.mp4')
if($LASTEXITCODE -ne 0){throw 'Failed to encode slower return'}
