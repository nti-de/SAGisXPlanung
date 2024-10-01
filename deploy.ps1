
<#
.Synopsis
   Builds and deploys SAGis XPlanung
#>

# osgeo: path to osgeo shell
# out: deploy location
# compiled: compiled to c or plain python (default)

param(
    [Parameter(Mandatory=$true)]
    [ValidateNotNullOrEmpty()]
    [string]$osgeo,

    [Parameter()]
    [string]$SrcDir = "src\SAGisXPlanung",

    [Parameter()]
    [string]$Out,

    [Parameter()]
    [switch]$Compiled,

    [Parameter()]
    [switch]$Clean,

    [Parameter()]
    [switch]$BuildDocs = $true
)

$plugin_src_path = Get-Location

Set-Location -Path $osgeo

# setup osgeo environment variables
if (Test-Path "OSGeo4W.bat" -PathType leaf ) {
   Write-Host "= Setup OSGeo4W Environment Variables" -ForegroundColor Yellow
   & $PSScriptRoot\Invoke-Environment.ps1 -Command "OSGeo4W.bat o4w_env"
}
else
{ Write-Host "= OSGeo4W shell not found!" -ForegroundColor Red}

Set-Location -Path $plugin_src_path

if ($Compiled.IsPresent) {
    Write-Host "= Compiling Plugin with Cython" -ForegroundColor Yellow

    python3 setup.py build_ext --inplace -f
}

Set-Location -Path "$plugin_src_path\$SrcDir"

if ($Out) {
    Write-Host "= Copy files to Output directory" -ForegroundColor Yellow
    Copy-Item "$plugin_src_path\$SrcDir\*" "$Out\SAGisXPlanung" -Exclude @("dependencies") -Recurse -Container -Force
}
else {
    $Out = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\"
    if ($Clean.IsPresent) {
        Write-Host "= Delete existing plugin" -ForegroundColor Yellow
        Remove-Item "$Out\SAGisXPlanung" -Recurse -Force -ErrorAction Ignore
    }
    Write-Host "= Copy files to QGIS Plugin directory" -ForegroundColor Yellow
    Write-Host "Copy from: $plugin_src_path\$SrcDir"
    Write-Host "Copy to: $Out\SAGisXPlanung"
    Copy-Item "$plugin_src_path\$SrcDir\*" "$Out\SAGisXPlanung" -Exclude @("dependencies") -Recurse -Container -Force
}

# delete all source files in output and all compiled files in source directory
if ($Compiled.IsPresent) {
    Write-Host "= Cleanup..." -ForegroundColor Yellow

    Write-Host "Deleting compiled files in source directory..."
    Set-Location -Path "$plugin_src_path\$SrcDir"
    Get-ChildItem *.pyd -Recurse | foreach { Remove-Item -Path $_.FullName }
    Get-ChildItem *.c -Recurse | foreach { Remove-Item -Path $_.FullName }

    Write-Host "Deleting source files in output directory..."
    Set-Location -Path "$Out\SAGisXPlanung"
    Get-ChildItem *.c -Recurse | foreach { Remove-Item -Path $_.FullName }

    Get-ChildItem *.py -File -Recurse | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item
}


function Build-Documentation {
    Write-Host "= Building Documentation" -ForegroundColor Yellow

    # Navigate to the docs directory
    Set-Location -Path "$plugin_src_path\docs"

    # Run the mkdocs build command
    python3 -m mkdocs build

    # Define the source and destination paths for the documentation
    $docsSource = "$plugin_src_path\docs\site\*"
    $docsDestination = "$Out\SAGisXPlanung\docs"

    # Ensure the destination directory exists
    if (!(Test-Path -Path $docsDestination)) {
        New-Item -ItemType Directory -Path $docsDestination | Out-Null
    }

    # Copy the built documentation to the destination
    Write-Host "= Copying built documentation to $docsDestination" -ForegroundColor Yellow
    Copy-Item -Path $docsSource -Destination $docsDestination -Recurse -Force
}


if ($BuildDocs.IsPresent) {
    Build-Documentation
}

Set-Location -Path "$plugin_src_path"


