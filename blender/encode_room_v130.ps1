param([ValidateSet('130','131','132','134','136')][string]$Revision = '130')
$ErrorActionPreference = 'Stop'
$roomSource = Join-Path $PSScriptRoot "outputs/web-room-v$Revision"
$roomPublish = Join-Path (Split-Path $PSScriptRoot -Parent) "public/room/v$Revision"
New-Item -ItemType Directory -Path $roomPublish -Force | Out-Null
$roomOrder = if ($Revision -ne '130') { @('idle','monitor-in','monitor-out','vinyl-in','vinyl-out','diploma-in','diploma-out') } else { @('monitor-in','monitor-out','idle','vinyl-in','vinyl-out','diploma-in','diploma-out') }
foreach ($roomClip in $roomOrder) {
    $roomCount = if ($roomClip -eq 'idle') { 240 } elseif ($roomClip.StartsWith('monitor')) { 121 } else { 73 }
    $roomFolder = Join-Path $roomSource $roomClip
    $roomDeadline = (Get-Date).AddMinutes(50)
    do {
        $roomFiles = @(Get-ChildItem -LiteralPath $roomFolder -Filter *.png -ErrorAction SilentlyContinue)
        if ((Get-Date) -gt $roomDeadline) { throw "Render timed out: $roomClip" }
        if ($roomFiles.Count -lt $roomCount) { Start-Sleep -Seconds 5 }
    } while ($roomFiles.Count -lt $roomCount)
    Start-Sleep -Seconds 2
    & ffmpeg -hide_banner -loglevel error -y -framerate 24 -i (Join-Path $roomFolder '%04d.png') -frames:v $roomCount -c:v libx264 -threads 4 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $roomPublish "$roomClip.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $roomClip" }
    Write-Output "V130_ENCODED $roomClip"
}
foreach ($roomStill in @(@('idle/0000.png','greeting.webp'),@('diploma-in/0072.png','diploma.webp'),@('vinyl-background/0000.png','vinyl-background.webp'),@('vinyl-still/0000.png','vinyl-still.webp'))) {
    & ffmpeg -hide_banner -loglevel error -y -i (Join-Path $roomSource $roomStill[0]) -quality 95 (Join-Path $roomPublish $roomStill[1])
    if ($LASTEXITCODE -ne 0) { throw 'Still encoding failed' }
}
if ($Revision -eq '136') {
    # White RGB with a compact 16-level coverage alpha for the pointer glow.
    $roomMaskSource = Join-Path $roomSource 'room-visible.png'
    & ffmpeg -hide_banner -loglevel error -y -i $roomMaskSource -i $roomMaskSource -filter_complex '[0:v]format=rgb24,lutrgb=r=255:g=255:b=255[c];[1:v]format=gray,lut=y=round(val/17)*17[a];[c][a]alphamerge' -compression_level 9 -pred mixed -frames:v 1 (Join-Path $roomPublish 'room-outline-mask.png')
    if ($LASTEXITCODE -ne 0) { throw 'Pointer mask encoding failed' }
}
Write-Output 'V130_ENCODING_COMPLETE'
