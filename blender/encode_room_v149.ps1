param([switch]$PlatesOnly)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'outputs/web-room-v149'
$publish = Join-Path (Split-Path $PSScriptRoot -Parent) 'public/room/v149'
New-Item -ItemType Directory -Force -Path $publish | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'shelf-geometry.json') -Destination (Join-Path $publish 'shelf-geometry.json')
foreach ($name in @('books-still','books-background','vinyl-still','vinyl-background','photos-still','photos-background','greeting-probe')) {
    $dest = if ($name -eq 'greeting-probe') { 'greeting' } else { $name }
    & ffmpeg -v error -y -i (Join-Path $source "$name/0000.png") -quality 95 (Join-Path $publish "$dest.webp")
    if ($LASTEXITCODE -ne 0) { throw "Plate encoding failed: $name" }
}
if ($PlatesOnly) { exit }
foreach ($name in @('shelf-1-0','shelf-0-1','shelf-1-2','shelf-2-1','vinyl-in','vinyl-out','idle','monitor-in','monitor-out','diploma-in','diploma-out')) {
    $count = if ($name -like 'shelf-*') { 37 } elseif ($name -eq 'idle') { 240 } elseif ($name -like 'monitor-*') { 121 } else { 73 }
    $folder = Join-Path $source $name
    for ($frame = 0; $frame -lt $count; $frame++) {
        $path = Join-Path $folder ('{0:D4}.png' -f $frame)
        if (!(Test-Path -LiteralPath $path)) { throw "Missing render: $path" }
    }
    & ffmpeg -v error -y -framerate 24 -i (Join-Path $folder '%04d.png') -frames:v $count -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $publish "$name.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $name" }
    Write-Output "V149_ENCODED $name"
}
& ffmpeg -v error -y -i (Join-Path $source 'diploma-in/0072.png') -quality 95 (Join-Path $publish 'diploma.webp')
if ($LASTEXITCODE -ne 0) { throw 'Diploma plate encoding failed' }
$mask = Join-Path $source 'room-visible.png'
& ffmpeg -hide_banner -loglevel error -y -i $mask -i $mask -filter_complex '[0:v]format=rgb24,lutrgb=r=255:g=255:b=255[c];[1:v]format=gray,lut=y=round(val/17)*17[a];[c][a]alphamerge' -compression_level 9 -pred mixed -frames:v 1 (Join-Path $publish 'room-outline-mask.png')
if ($LASTEXITCODE -ne 0) { throw 'Hover mask encoding failed' }
Write-Output 'V149_ENCODING_COMPLETE'
