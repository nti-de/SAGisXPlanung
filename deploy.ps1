<#
.Synopsis
Builds and deploys a QGIS plugin
#>

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

# Root of the plugin project
$plugin_src_path = Get-Location

# Derive plugin name from source directory
$PluginName = Split-Path $SrcDir -Leaf
Write-Host "= Deploying plugin: $PluginName" -ForegroundColor Cyan

# ---------------------------------------------------------------------
# Setup OSGeo environment
# ---------------------------------------------------------------------
Set-Location -Path $osgeo

if (Test-Path "OSGeo4W.bat" -PathType leaf ) {
   Write-Host "= Setup OSGeo4W Environment Variables" -ForegroundColor Yellow
   & $PSScriptRoot\Invoke-Environment.ps1 -Command "OSGeo4W.bat o4w_env"
}
else
{ Write-Host "= OSGeo4W shell not found!" -ForegroundColor Red}

Set-Location -Path $plugin_src_path

# ---------------------------------------------------------------------
# Compile plugin (optional)
# ---------------------------------------------------------------------
if ($Compiled.IsPresent) {
    Write-Host "= Compiling Plugin with Cython" -ForegroundColor Yellow
    python3 setup.py build_ext --inplace -f
}

# ---------------------------------------------------------------------
# Copy plugin files
# ---------------------------------------------------------------------
Set-Location -Path "$plugin_src_path\$SrcDir"

if ($Out) {
    Write-Host "= Copy files to Output directory" -ForegroundColor Yellow
    Copy-Item "$plugin_src_path\$SrcDir\*" "$Out\$PluginName" -Exclude @("dependencies") -Recurse -Container -Force
}
else {
    $Out = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\"
    if ($Clean.IsPresent) {
        Write-Host "= Delete existing plugin" -ForegroundColor Yellow
        Remove-Item "$Out\$PluginName" -Recurse -Force -ErrorAction Ignore
    }
    Write-Host "= Copy files to QGIS Plugin directory" -ForegroundColor Yellow
    Write-Host "Copy from: $plugin_src_path\$SrcDir"
    Write-Host "Copy to: $Out\$PluginName"
    Copy-Item "$plugin_src_path\$SrcDir\*" "$Out\$PluginName" -Exclude @("dependencies") -Recurse -Container -Force
}

# ---------------------------------------------------------------------
# Cleanup compiled / source artifacts
# ---------------------------------------------------------------------
if ($Compiled.IsPresent) {
    Write-Host "= Cleanup..." -ForegroundColor Yellow

    Write-Host "Deleting compiled files in source directory..."
    Set-Location -Path "$plugin_src_path\$SrcDir"
    Get-ChildItem *.pyd -Recurse | foreach { Remove-Item -Path $_.FullName }
    Get-ChildItem *.c -Recurse | foreach { Remove-Item -Path $_.FullName }

    Write-Host "Deleting source files in output directory..."
    Set-Location -Path "$Out\$PluginName"
    Get-ChildItem *.c -Recurse | foreach { Remove-Item -Path $_.FullName }

    Get-ChildItem *.py -File -Recurse | Where-Object { $_.Name -ne "__init__.py" } | Remove-Item
}


function Build-Documentation {
    Write-Host "= Building Documentation" -ForegroundColor Yellow

    # Navigate to the docs directory
    Set-Location -Path "$plugin_src_path\docs"

    # Run the zensical build command
    python3 -m zensical build

    # Define the source and destination paths for the documentation
    $docsSource = "$plugin_src_path\docs\site\*"
    $docsDestination = "$Out\$PluginName\docs"

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


