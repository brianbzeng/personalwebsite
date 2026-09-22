$ErrorActionPreference = 'Stop'
$roomRepo = Split-Path $PSScriptRoot -Parent
$roomSource = Join-Path $PSScriptRoot 'outputs/web-room-v125'
$roomPublic = Join-Path $roomRepo 'public/room'
foreach ($roomClip in @('vinyl-in','vinyl-out','diploma-in','diploma-out','monitor-in','monitor-out','idle')) {
    $roomCount = if ($roomClip -eq 'idle') { 120 } else { 73 }
    $roomFolder = Join-Path $roomSource $roomClip
    $roomDeadline = (Get-Date).AddMinutes(30)
    do {
        $roomFiles = @(Get-ChildItem -LiteralPath $roomFolder -Filter *.png -ErrorAction SilentlyContinue)
        if ((Get-Date) -gt $roomDeadline) { throw "Render timed out: $roomClip" }
        if ($roomFiles.Count -lt $roomCount) { Start-Sleep -Seconds 5 }
    } while ($roomFiles.Count -lt $roomCount)
    # Let the last PNG close before the encoder reads it.
    Start-Sleep -Seconds 2
    $roomInput = Join-Path $roomFolder '%04d.png'
    $roomOutput = Join-Path $roomPublic "$roomClip.mp4"
    if ($roomClip -eq 'idle') {
        & ffmpeg -hide_banner -loglevel error -y -framerate 24 -i $roomInput -filter_complex '[0:v]split[a][b];[a]trim=start=0.5,setpts=PTS-STARTPTS[c];[b]trim=end=0.5,setpts=PTS-STARTPTS[d];[c][d]xfade=transition=fade:duration=0.5:offset=4[v]' -map '[v]' -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an $roomOutput
    } else {
        & ffmpeg -hide_banner -loglevel error -y -framerate 24 -i $roomInput -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an $roomOutput
    }
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $roomClip" }
    Write-Output "ENCODED $roomClip $((Get-Item -LiteralPath $roomOutput).Length) bytes"
}
foreach ($roomStill in @(@('idle/0000.png','greeting.webp'),@('diploma-in/0072.png','diploma.webp'),@('vinyl-background/0000.png','vinyl-background.webp'))) {
    & ffmpeg -hide_banner -loglevel error -y -i (Join-Path $roomSource $roomStill[0]) -quality 95 (Join-Path $roomPublic $roomStill[1])
    if ($LASTEXITCODE -ne 0) { throw 'Still encoding failed' }
}
Write-Output 'RELEASE_MEDIA_COMPLETE'
