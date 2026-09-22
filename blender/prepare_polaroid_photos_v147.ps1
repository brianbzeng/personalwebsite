# Deterministic crop, grayscale matrix and resize only. No generative edits.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$projectRoot = Split-Path $PSScriptRoot -Parent
$assetDir = Join-Path $projectRoot 'public/room/polaroid-art/v147'
$sourceDir = Join-Path $projectRoot 'blender/assets/polaroids/v147-originals'
$specs = @(
    @{ File='codex-clipboard-0e41dd1d-f495-45a2-bb18-455e86ee2f83.png'; X=0; Y=256; Size=768 },
    @{ File='codex-clipboard-454b3b51-2f48-4a9c-ad2d-56e8c80289ce.png'; X=220; Y=119; Size=650 },
    @{ File='codex-clipboard-ce5c4898-97d9-49a2-9e76-15de83ef53aa.png'; X=120; Y=0; Size=769 },
    @{ File='codex-clipboard-50701592-9440-4e70-b13b-a932caf160b5.png'; X=0; Y=170; Size=768 }
)
New-Item -ItemType Directory -Force -Path $assetDir,$sourceDir | Out-Null
$matrix = New-Object System.Drawing.Imaging.ColorMatrix
$matrix.Matrix00=.299; $matrix.Matrix01=.299; $matrix.Matrix02=.299
$matrix.Matrix10=.587; $matrix.Matrix11=.587; $matrix.Matrix12=.587
$matrix.Matrix20=.114; $matrix.Matrix21=.114; $matrix.Matrix22=.114
$attributes = New-Object System.Drawing.Imaging.ImageAttributes
$attributes.SetColorMatrix($matrix)
$attributes.SetWrapMode([System.Drawing.Drawing2D.WrapMode]::TileFlipXY)
$audit = @()
for($i=0; $i -lt $specs.Count; $i++) {
    $spec=$specs[$i]
    $source=Join-Path 'C:/Users/BRIANZ~1/AppData/Local/Temp' $spec.File
    $output=Join-Path $assetDir ('photo-{0}.png' -f ($i+1))
    if(Test-Path -LiteralPath $output){ throw "Preserve existing output: $output" }
    $original=[System.Drawing.Image]::FromFile($source)
    if(($spec.X+$spec.Size) -gt $original.Width -or ($spec.Y+$spec.Size) -gt $original.Height){throw 'Crop exceeds source'}
    $bitmap=New-Object System.Drawing.Bitmap 512,512
    $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $rect=New-Object System.Drawing.Rectangle 0,0,512,512
    $graphics.DrawImage($original,$rect,[single]$spec.X,[single]$spec.Y,[single]$spec.Size,[single]$spec.Size,[System.Drawing.GraphicsUnit]::Pixel,$attributes)
    $bitmap.Save($output,[System.Drawing.Imaging.ImageFormat]::Png)
    $audit+=@{order=$i+1;source=$spec.File;sourceSha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash;crop=@($spec.X,$spec.Y,$spec.Size,$spec.Size);outputSize=@(512,512);method='GDI+ grayscale ColorMatrix and bicubic resize; no generated pixels except resampling'}
    $graphics.Dispose();$bitmap.Dispose();$original.Dispose()
    Copy-Item -LiteralPath $source -Destination (Join-Path $sourceDir ('photo-{0}-original.png' -f ($i+1)))
}
$attributes.Dispose()
$audit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $sourceDir 'processing-audit.json')
Write-Output 'Four faithful grayscale crops saved; originals retained.'
