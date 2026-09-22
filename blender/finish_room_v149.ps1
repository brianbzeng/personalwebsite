param([Parameter(Mandatory=$true)][int]$RenderProcessId)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$output=Join-Path $PSScriptRoot 'outputs/web-room-v149'
$scene=Join-Path $PSScriptRoot 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v149-approved-project-covers.blend'
$process=Get-CimInstance Win32_Process -Filter "ProcessId=$RenderProcessId"
if ($process -and ($process.Name -ne 'blender.exe' -or $process.CommandLine -notlike '*v149-approved-project-covers.blend*')) { throw 'Unexpected render process; refusing to wait on unrelated work' }
while (Get-Process -Id $RenderProcessId -ErrorAction SilentlyContinue) {
    Start-Sleep -Seconds 45
    $count=0
    foreach ($folder in Get-ChildItem -LiteralPath $output -Directory) { $count += @(Get-ChildItem -LiteralPath $folder.FullName -Filter '*.png').Count }
    Write-Output "V149_RENDER_PROGRESS $count / 929"
}
if (!(Test-Path -LiteralPath (Join-Path $output 'diploma-out/0072.png'))) { throw 'Render ended without its final frame' }
& 'D:/Blender5.2/blender.exe' -b $scene --python (Join-Path $PSScriptRoot 'prepare_room_render_v149.py') --python (Join-Path $PSScriptRoot 'render_shelf_v137.py') -- --v149 --greeting-only --refresh-greeting
if ($LASTEXITCODE -ne 0) { throw 'Corrected greeting render failed' }
& 'D:/Blender5.2/blender.exe' -b $scene --python (Join-Path $PSScriptRoot 'prepare_room_render_v149.py') --python (Join-Path $PSScriptRoot 'render_hover_mask_v130.py') -- --v149
if ($LASTEXITCODE -ne 0) { throw 'Outline mask render failed' }
& (Join-Path $PSScriptRoot 'encode_room_v149.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Media encoding failed' }
& node (Join-Path $PSScriptRoot 'verify_room_v149.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Release verification needs attention' }
Write-Output 'V149_READY_FOR_SITE_SWITCH'
