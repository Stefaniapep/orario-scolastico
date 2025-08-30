# Release Helper Script for GeneraOrarioApp (PowerShell version)
# Usage: .\release.ps1 [version] [-BuildOnly] [-CommitOnly]

param(
    [string]$Version = "",
    [switch]$BuildOnly = $false,
    [switch]$CommitOnly = $false,
    [switch]$Help = $false
)

# Function to print colored output
function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to get current version from version.py
function Get-CurrentVersion {
    return python -c "from version import get_version; print(get_version())"
}

# Function to update version in version.py
function Update-Version {
    param([string]$NewVersion)
    
    Write-ColoredOutput "Updating version.py to version $NewVersion..." "Yellow"
    
    # Backup current version.py
    Copy-Item "version.py" "version.py.bak"
    
    # Update version
    $content = Get-Content "version.py" -Raw
    $content = $content -replace '__version__ = ".*"', "__version__ = `"$NewVersion`""
    $content | Set-Content "version.py" -NoNewline
    
    Write-ColoredOutput "Version updated to $NewVersion" "Green"
}

# Function to commit and push version change
function Commit-VersionChange {
    param([string]$Version)
    
    Write-ColoredOutput "Committing version change to trigger GitHub Actions..." "Yellow"
    
    # Add and commit version change
    git add version.py
    $commitMessage = "Release v$Version - Update version info"
    git commit -m $commitMessage
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredOutput "Version change committed successfully" "Green"
        Write-ColoredOutput "Pushing to trigger GitHub Actions..." "Yellow"
        
        git push origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColoredOutput "✅ Push successful! GitHub Actions should start building..." "Green"
            Write-ColoredOutput "Monitor the build at: https://github.com/Stefaniapep/orario-scolastico/actions" "Blue"
        } else {
            Write-ColoredOutput "❌ Push failed! Please check your Git configuration." "Red"
            return $false
        }
    } else {
        Write-ColoredOutput "❌ Commit failed! Please check if there are changes to commit." "Red"
        return $false
    }
    
    return $true
}

# Function to build locally
function Build-Local {
    param([string]$Version)
    
    Write-ColoredOutput "Building GeneraOrarioApp v$Version locally..." "Yellow"
    
    # Check dependencies
    Write-ColoredOutput "Checking dependencies..." "Blue"
    try {
        python -c "import streamlit, ortools, pandas, openpyxl; print('✓ All dependencies available')"
    } catch {
        Write-ColoredOutput "✗ Missing dependencies! Run: pip install -r requirements.txt" "Red"
        return $false
    }
    
    # Run PyInstaller
    Write-ColoredOutput "Running PyInstaller..." "Blue"
    
    $pyinstallerArgs = @(
        "--clean"
        "--name", "GeneraOrarioApp"
        "--onefile"
        "--console"
        "--add-data", "app.py;."
        "--add-data", "config.json;."
        "--add-data", "version.py;."
        "--collect-all", "streamlit"
        "--collect-all", "ortools"
        "--noconfirm"
        "streamlit_wrapper.py"
    )
    
    & pyinstaller @pyinstallerArgs
    
    if (Test-Path "dist\GeneraOrarioApp.exe") {
        $size = (Get-Item "dist\GeneraOrarioApp.exe").Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-ColoredOutput "✓ Build successful! Executable size: ${sizeMB}MB" "Green"
        Write-ColoredOutput "Executable location: dist\GeneraOrarioApp.exe" "Blue"
        return $true
    } else {
        Write-ColoredOutput "✗ Build failed - executable not found!" "Red"
        return $false
    }
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\release.ps1 [version] [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -CommitOnly  Only update version and commit (triggers GitHub Actions)"
    Write-Host "  -BuildOnly   Only build locally, don't commit/push"
    Write-Host "  -Help        Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\release.ps1 1.2.0                # Update version, commit & push (triggers CI/CD)"
    Write-Host "  .\release.ps1 1.2.0 -CommitOnly    # Only update version and commit/push"
    Write-Host "  .\release.ps1 1.2.0 -BuildOnly     # Only update version and build locally"
    Write-Host "  .\release.ps1 -BuildOnly           # Build with current version"
    Write-Host ""
    Write-Host "NEW WORKFLOW:"
    Write-Host "1. Update version.py and push → GitHub Actions builds & releases automatically"
    Write-Host "2. No manual tagging needed - GitHub Actions creates tags after successful build"
    Write-Host ""
    Write-Host "Current version: $(Get-CurrentVersion)"
}

# Main script logic
function Main {
    if ($Help) {
        Show-Usage
        return
    }
    
    # If no version specified and not build-only, ask for it
    if ([string]::IsNullOrEmpty($Version) -and -not $BuildOnly) {
        $currentVersion = Get-CurrentVersion
        Write-ColoredOutput "Current version: $currentVersion" "Yellow"
        $Version = Read-Host "Enter new version (e.g., 1.2.0)"
        if ([string]::IsNullOrEmpty($Version)) {
            Write-ColoredOutput "Version is required" "Red"
            return
        }
    }
    
    # Use current version if build-only and no version specified
    if ([string]::IsNullOrEmpty($Version) -and $BuildOnly) {
        $Version = Get-CurrentVersion
        Write-ColoredOutput "Using current version: $Version" "Blue"
    }
    
    # Validate version format
    if ($Version -notmatch '^\d+\.\d+\.\d+$') {
        Write-ColoredOutput "Invalid version format. Use semantic versioning (e.g., 1.2.0)" "Red"
        return
    }
    
    Write-ColoredOutput "=== GeneraOrarioApp Release Process ===" "Blue"
    Write-ColoredOutput "Version: $Version" "Blue"
    Write-ColoredOutput "New Workflow: version.py commit → GitHub Actions → automatic tag & release" "Cyan"
    
    # Update version in version.py
    $currentVersion = Get-CurrentVersion
    if ($Version -ne $currentVersion) {
        Update-Version $Version
    }
    
    # Execute based on options
    if ($BuildOnly) {
        $success = Build-Local $Version
        if (-not $success) {
            return
        }
    } elseif ($CommitOnly) {
        $success = Commit-VersionChange $Version
        if (-not $success) {
            return
        }
    } else {
        # Default: commit and push to trigger CI/CD
        $success = Commit-VersionChange $Version
        if (-not $success) {
            return
        }
        Write-ColoredOutput "" "Blue"
        Write-ColoredOutput "🚀 GitHub Actions should now:" "Yellow"
        Write-ColoredOutput "  1. Detect the version.py change" "Blue"
        Write-ColoredOutput "  2. Build the Windows executable" "Blue"
        Write-ColoredOutput "  3. Create tag v$Version automatically" "Blue"
        Write-ColoredOutput "  4. Publish the release on GitHub" "Blue"
        Write-ColoredOutput "" "Blue"
        Write-ColoredOutput "Monitor progress at:" "Yellow"
        Write-ColoredOutput "https://github.com/Stefaniapep/orario-scolastico/actions" "Blue"
    }
    
    Write-ColoredOutput "=== Release process completed! ===" "Green"
}

# Run main function
Main
