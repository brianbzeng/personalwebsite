param([ValidateSet('162','163')][string]$Version = '162')
$ErrorActionPreference = 'Stop'
$taskMediaRoot = Join-Path (Split-Path $PSScriptRoot -Parent) "public/room/v$Version"
New-Item -ItemType Directory -Force -Path $taskMediaRoot | Out-Null
$taskClips = @(
    @('web-room-v162','idle',240,24),
    @('web-room-v162','monitor-in',121,24), @('web-room-v162','monitor-out',121,24),
    @('web-room-v162','diploma-in',73,24), @('web-room-v162','diploma-out',73,24),
    @('web-room-v162-shelf','vinyl-in',73,24), @('web-room-v162-shelf','vinyl-out',73,24),
    @('web-room-v162-photos','photos-in',91,30), @('web-room-v162-photos','photos-out',91,30),
    @('web-room-v162-photos','shelf-1-2',37,24), @('web-room-v162-photos','shelf-2-1',37,24)
)
foreach ($taskClip in $taskClips) {
    $taskRoot = Join-Path $PSScriptRoot ("outputs/$($taskClip[0])/$($taskClip[1])" -replace 'v162',"v$Version")
    for ($i=0; $i -lt $taskClip[2]; $i++) {
        if (!(Test-Path -LiteralPath (Join-Path $taskRoot ('{0:D4}.png' -f $i)))) { throw "Missing $taskRoot frame $i" }
    }
    & ffmpeg -v error -y -framerate $taskClip[3] -i "$taskRoot/%04d.png" -frames:v $taskClip[2] -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $taskMediaRoot "$($taskClip[1]).mp4")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $taskRoot" }
}
foreach ($taskStill in @(@('web-room-v162/greeting-probe/0000.png','greeting'),@('web-room-v162/diploma-in/0072.png','diploma'),@('web-room-v162-photos/photos-still.png','photos-still'),@('web-room-v162-photos/photos-background.png','photos-background'))) {
    & ffmpeg -v error -y -i (Join-Path $PSScriptRoot ("outputs/$($taskStill[0])" -replace 'v162',"v$Version")) -c:v libwebp -lossless 1 (Join-Path $taskMediaRoot "$($taskStill[1]).webp")
    if ($LASTEXITCODE -ne 0) { throw "Still encoding failed" }
}
