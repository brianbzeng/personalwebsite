param([ValidateSet(153,154)][int]$Version=153)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot "outputs/web-room-v$Version"
$publish = Join-Path (Split-Path $PSScriptRoot -Parent) "public/room/v$Version"
New-Item -ItemType Directory -Force -Path $publish | Out-Null
foreach ($name in @('photos-in', 'photos-out')) {
    for ($frame = 0; $frame -lt 91; $frame++) {
        $path = Join-Path (Join-Path $source $name) ('{0:D4}.png' -f $frame)
        if (!(Test-Path -LiteralPath $path)) { throw "Missing render: $path" }
    }
    & ffmpeg -v error -y -framerate 30 -i (Join-Path (Join-Path $source $name) '%04d.png') -frames:v 91 -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $publish "$name.mp4")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $name" }
    Write-Output "V153_ENCODED $name"
}
if ($Version -eq 154) {
    & ffmpeg -v error -y -i (Join-Path $source 'photos-in/0090.png') -quality 95 (Join-Path $publish 'photos-still.webp')
    if ($LASTEXITCODE -ne 0) { throw 'Photo still encoding failed' }
}
