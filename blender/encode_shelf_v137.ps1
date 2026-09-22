param([switch]$PlatesOnly)
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'outputs/web-room-v137'
$publish=Join-Path (Split-Path $PSScriptRoot -Parent) 'public/room/v137'
New-Item -ItemType Directory -Force -Path $publish | Out-Null
Copy-Item -LiteralPath (Join-Path $source 'shelf-geometry.json') -Destination (Join-Path $publish 'shelf-geometry.json')
# No object moved in the greeting view; the existing contour mask stays exact.
Copy-Item -LiteralPath (Join-Path (Split-Path $publish -Parent) 'v136/room-outline-mask.png') -Destination (Join-Path $publish 'room-outline-mask.png')
foreach($name in @('books-still','books-background','vinyl-still','vinyl-background','photos-still','photos-background','greeting-probe')) {
    $dest=if($name -eq 'greeting-probe'){'greeting'}else{$name}
    & ffmpeg -v error -y -i (Join-Path $source "$name/0000.png") -quality 95 (Join-Path $publish "$dest.webp")
    if($LASTEXITCODE -ne 0){throw "Plate encoding failed: $name"}
}
if($PlatesOnly){exit}
foreach($name in @('shelf-1-0','shelf-0-1','shelf-1-2','shelf-2-1','vinyl-in','vinyl-out','idle','monitor-in','monitor-out','diploma-in','diploma-out')) {
    $count=if($name -like 'shelf-*'){37}elseif($name -eq 'idle'){240}elseif($name -like 'monitor-*'){121}else{73}
    $folder=Join-Path $source $name
    $deadline=(Get-Date).AddMinutes(50)
    do {
        $files=@(Get-ChildItem -LiteralPath $folder -Filter '*.png' -ErrorAction SilentlyContinue)
        if((Get-Date) -gt $deadline){throw "Render timeout: $name"}
        if($files.Count -lt $count){Start-Sleep -Seconds 5}
    }while($files.Count -lt $count)
    Start-Sleep -Seconds 2
    & ffmpeg -v error -y -framerate 24 -i (Join-Path $folder '%04d.png') -frames:v $count -c:v libx264 -threads 3 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -an (Join-Path $publish "$name.mp4")
    if($LASTEXITCODE -ne 0){throw "Encoding failed: $name"}
    Write-Output "V137_ENCODED $name"
}
& ffmpeg -v error -y -i (Join-Path $source 'diploma-in/0072.png') -quality 95 (Join-Path $publish 'diploma.webp')
Write-Output 'V137_ENCODING_COMPLETE'
