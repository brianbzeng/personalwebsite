$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$sourceRoot=Join-Path $PSScriptRoot 'outputs/web-room-v156/return'
$renderRoot=Join-Path $PSScriptRoot 'outputs/web-room-v157/return'
$mediaRoot=Join-Path $projectRoot 'public/room/v157'
New-Item -ItemType Directory -Force -Path $renderRoot,$mediaRoot | Out-Null
# Same rendered camera path; hold nine extra frames for the reversed arm,
# then preserve every original pan frame and hold the cubby for slot insertion.
for($frame=0;$frame -lt 47;$frame++){
  $sourceFrame=[Math]::Min(27,[Math]::Max(0,$frame-9))
  Copy-Item -LiteralPath (Join-Path $sourceRoot ('{0:0000}.png' -f $sourceFrame)) -Destination (Join-Path $renderRoot ('{0:0000}.png' -f $frame))
}
& ffmpeg -v error -y -framerate 24 -i (Join-Path $renderRoot '%04d.png') -c:v libx264 -crf 16 -preset slow -threads 3 -pix_fmt yuv420p -movflags +faststart (Join-Path $mediaRoot 'return-background.mp4')
if($LASTEXITCODE -ne 0){throw 'Failed to encode revised return'}
