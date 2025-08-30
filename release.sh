#!/bin/bash
# Release Helper Script for GeneraOrarioApp
# Usage: ./release.sh [version] [--commit-only] [--build-only]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to get current version from version.py
get_current_version() {
    python -c "from version import get_version; print(get_version())"
}

# Function to update version in version.py
update_version() {
    local new_version=$1
    print_color $YELLOW "Updating version.py to version $new_version..."
    
    # Backup current version.py
    cp version.py version.py.bak
    
    # Update version
    sed -i "s/__version__ = \".*\"/__version__ = \"$new_version\"/" version.py
    
    print_color $GREEN "Version updated to $new_version"
}

# Function to commit and push version change
commit_version_change() {
    local version=$1
    
    print_color $YELLOW "Committing version change to trigger GitHub Actions..."
    
    # Add and commit version change
    git add version.py
    local commit_message="Release v$version - Update version info"
    git commit -m "$commit_message"
    
    if [ $? -eq 0 ]; then
        print_color $GREEN "Version change committed successfully"
        print_color $YELLOW "Pushing to trigger GitHub Actions..."
        
        git push origin main
        
        if [ $? -eq 0 ]; then
            print_color $GREEN "✅ Push successful! GitHub Actions should start building..."
            print_color $BLUE "Monitor the build at: https://github.com/Stefaniapep/orario-scolastico/actions"
        else
            print_color $RED "❌ Push failed! Please check your Git configuration."
            return 1
        fi
    else
        print_color $RED "❌ Commit failed! Please check if there are changes to commit."
        return 1
    fi
    
    return 0
}

# Function to build locally
build_local() {
    local version=$1
    
    print_color $YELLOW "Building GeneraOrarioApp v$version locally..."
    
    # Check dependencies
    print_color $BLUE "Checking dependencies..."
    python -c "import streamlit, ortools, pandas, openpyxl; print('✓ All dependencies available')"
    
    # Run PyInstaller
    print_color $BLUE "Running PyInstaller..."
    pyinstaller --clean --name "GeneraOrarioApp" --onefile --console \
        --add-data "app.py;." \
        --add-data "config.json;." \
        --add-data "version.py;." \
        --collect-all streamlit \
        --collect-all ortools \
        --noconfirm streamlit_wrapper.py
    
    if [ -f "dist/GeneraOrarioApp.exe" ]; then
        local size=$(stat -f%z "dist/GeneraOrarioApp.exe" 2>/dev/null || stat -c%s "dist/GeneraOrarioApp.exe" 2>/dev/null || echo "unknown")
        local size_mb=$((size / 1024 / 1024))
        print_color $GREEN "✓ Build successful! Executable size: ${size_mb}MB"
        print_color $BLUE "Executable location: dist/GeneraOrarioApp.exe"
    else
        print_color $RED "✗ Build failed - executable not found!"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [version] [options]"
    echo ""
    echo "Options:"
    echo "  --commit-only  Only update version and commit (triggers GitHub Actions)"
    echo "  --build-only   Only build locally, don't commit/push"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 1.2.0                    # Update version, commit & push (triggers CI/CD)"
    echo "  $0 1.2.0 --commit-only      # Only update version and commit/push"
    echo "  $0 1.2.0 --build-only       # Only update version and build locally"
    echo "  $0 --build-only             # Build with current version"
    echo ""
    echo "NEW WORKFLOW:"
    echo "1. Update version.py and push → GitHub Actions builds & releases automatically"
    echo "2. No manual tagging needed - GitHub Actions creates tags after successful build"
    echo ""
    echo "Current version: $(get_current_version)"
}

# Main script logic
main() {
    local version=""
    local commit_only=false
    local build_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --commit-only)
                commit_only=true
                shift
                ;;
            --build-only)
                build_only=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            -*)
                print_color $RED "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$version" ]]; then
                    version=$1
                else
                    print_color $RED "Multiple versions specified: $version and $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # If no version specified and not build-only, ask for it
    if [[ -z "$version" && "$build_only" == false ]]; then
        print_color $YELLOW "Current version: $(get_current_version)"
        read -p "Enter new version (e.g., 1.2.0): " version
        if [[ -z "$version" ]]; then
            print_color $RED "Version is required"
            exit 1
        fi
    fi
    
    # Use current version if build-only and no version specified
    if [[ -z "$version" && "$build_only" == true ]]; then
        version=$(get_current_version)
        print_color $BLUE "Using current version: $version"
    fi
    
    # Validate version format
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_color $RED "Invalid version format. Use semantic versioning (e.g., 1.2.0)"
        exit 1
    fi
    
    print_color $BLUE "=== GeneraOrarioApp Release Process ==="
    print_color $BLUE "Version: $version"
    print_color $CYAN "New Workflow: version.py commit → GitHub Actions → automatic tag & release"
    
    # Update version in version.py
    if [[ "$version" != "$(get_current_version)" ]]; then
        update_version "$version"
    fi
    
    # Execute based on options
    if [[ "$build_only" == true ]]; then
        build_local "$version"
    elif [[ "$commit_only" == true ]]; then
        commit_version_change "$version"
    else
        # Default: commit and push to trigger CI/CD
        commit_version_change "$version"
        print_color $BLUE ""
        print_color $YELLOW "🚀 GitHub Actions should now:"
        print_color $BLUE "  1. Detect the version.py change"
        print_color $BLUE "  2. Build the Windows executable"
        print_color $BLUE "  3. Create tag v$version automatically"
        print_color $BLUE "  4. Publish the release on GitHub"
        print_color $BLUE ""
        print_color $YELLOW "Monitor progress at:"
        print_color $BLUE "https://github.com/Stefaniapep/orario-scolastico/actions"
    fi
    
    print_color $GREEN "=== Release process completed! ==="
}

# Run main function
main "$@"
