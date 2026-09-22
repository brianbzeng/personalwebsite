$ErrorActionPreference = 'Stop'
$roomRepo = Split-Path $PSScriptRoot -Parent
$roomSource = Join-Path $PSScriptRoot 'outputs/web-room-v127'
$roomPublic = Join-Path $roomRepo 'public/room'
foreach ($roomClip in @('idle','monitor-in','monitor-out','vinyl-in','vinyl-out','diploma-in','diploma-out')) {
    $roomCount = if ($roomClip -eq 'idle') { 240 } elseif ($roomClip.StartsWith('monitor')) { 121 } else { 73 }
    $roomFolder = Join-Path $roomSource $roomClip
    $roomDeadline = (Get-Date).AddMinutes(40)
    do {
        $roomFiles = @(Get-ChildItem -LiteralPath $roomFolder -Filter *.png -ErrorAction SilentlyContinue)
        if ((Get-Date) -gt $roomDeadline) { throw "Render timed out: $roomClip" }
        if ($roomFiles.Count -lt $roomCount) { Start-Sleep -Seconds 5 }
    } while ($roomFiles.Count -lt $roomCount)
    Start-Sleep -Seconds 2
    $roomInput = Join-Path $roomFolder '%04d.png'
    $roomOutput = Join-Path $roomSource "$roomClip.mp4"
    & ffmpeg -hide_banner -loglevel error -y -framerate 24 -i $roomInput -frames:v $roomCount -c:v libx264 -threads 4 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an $roomOutput
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $roomClip" }
    Copy-Item -LiteralPath $roomOutput -Destination (Join-Path $roomPublic "$roomClip.mp4") -Force
    Write-Output "ENCODED $roomClip $((Get-Item -LiteralPath $roomOutput).Length) bytes"
}
foreach ($roomStill in @(@('idle/0000.png','greeting.webp'),@('diploma-in/0072.png','diploma.webp'),@('vinyl-background/0000.png','vinyl-background.webp'),@('vinyl-still/0000.png','vinyl-still.webp'))) {
    & ffmpeg -hide_banner -loglevel error -y -i (Join-Path $roomSource $roomStill[0]) -quality 95 (Join-Path $roomPublic $roomStill[1])
    if ($LASTEXITCODE -ne 0) { throw 'Still encoding failed' }
}
& ffmpeg -hide_banner -loglevel error -y -i (Join-Path $roomSource 'floor-visible.png') -vf 'format=rgba,geq=r=255:g=255:b=255:a=if(lt(r(X\,Y)\,8)\,0\,r(X\,Y))' -compression_level 9 -frames:v 1 (Join-Path $roomPublic 'floor-grid-mask.png')
if ($LASTEXITCODE -ne 0) { throw 'Mask encoding failed' }
Write-Output 'CALM_MEDIA_COMPLETE'
