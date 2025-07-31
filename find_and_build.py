#!/usr/bin/env python3
"""
Find existing executable or build a new one
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta

def find_recent_executables():
    """Search for recently created .exe files that might be our installer."""
    print("🔍 Searching for recently created executables...")
    
    # Search directories
    search_dirs = [
        Path.cwd(),
        Path("C:/Users/Bario/OneDrive/Dokumente"),
        Path("C:/Users/Bario/OneDrive/Dokumente/download"),
        Path("C:/Users/Bario/OneDrive/Dokumente/download/exe"),
        Path("C:/Users/Bario/OneDrive/Dokumente/dist"),
        Path("dist"),
        Path("build"),
    ]
    
    # Look for files created in the last 2 hours
    cutoff_time = datetime.now() - timedelta(hours=2)
    found_files = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        print(f"   Checking: {search_dir}")
        
        try:
            for exe_file in search_dir.rglob("*.exe"):
                # Check if file was created recently
                created_time = datetime.fromtimestamp(exe_file.stat().st_ctime)
                
                if created_time > cutoff_time:
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    found_files.append({
                        'path': exe_file,
                        'size_mb': size_mb,
                        'created': created_time
                    })
        except (PermissionError, OSError):
            continue
    
    return found_files

def simple_build():
    """Simple, direct PyInstaller build without complex spec files."""
    print("\n🔨 Starting simple build...")
    
    source = r"C:\Users\Bario\OneDrive\Dokumente\download\MintyInstall.py"
    icon = r"C:\Users\Bario\OneDrive\Dokumente\square_icon.ico"
    output_dir = r"C:\Users\Bario\OneDrive\Dokumente\download\exe"
    
    # Verify source exists
    if not Path(source).exists():
        print(f"❌ Source file not found: {source}")
        return False
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Clean previous builds
    for cleanup_dir in ["build", "dist"]:
        if Path(cleanup_dir).exists():
            shutil.rmtree(cleanup_dir)
            print(f"🧹 Cleaned {cleanup_dir}")
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable
        "--windowed",                   # No console
        "--name", "MintyInstall",
        "--distpath", output_dir,       # Output directory
    ]
    
    # Add icon if it exists
    if Path(icon).exists():
        cmd.extend(["--icon", icon])
        print(f"✅ Using icon: {icon}")
    else:
        print(f"⚠️  Icon not found: {icon}")
    
    # Add hidden imports for our application
    hidden_imports = [
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtNetwork",
        "platform", "subprocess", "pathlib", "json", "urllib.request"
    ]
    
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Add source file last
    cmd.append(source)
    
    print("📦 Running PyInstaller...")
    print(f"Command: {' '.join(cmd[:5])} ... [truncated]")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("STDOUT:", e.stdout[-500:] if e.stdout else "None")
        print("STDERR:", e.stderr[-500:] if e.stderr else "None")
        return False

def main():
    print("=" * 60)
    print("BetterMint Modded Installer - Find & Build")
    print("=" * 60)
    
    # First, search for existing executables
    found_files = find_recent_executables()
    
    if found_files:
        print(f"\n✅ Found {len(found_files)} recent executable(s):")
        for i, file_info in enumerate(found_files):
            print(f"   {i+1}. {file_info['path']}")
            print(f"      Size: {file_info['size_mb']:.1f} MB")
            print(f"      Created: {file_info['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        # Check if any look like our installer
        installer_files = [f for f in found_files if "BetterMint" in str(f['path']) or f['size_mb'] > 50]
        
        if installer_files:
            best_match = max(installer_files, key=lambda x: x['created'])
            print(f"🎯 Best match: {best_match['path']}")
            
            # Ask user what to do
            choice = input("Found potential installer. (T)est it, (M)ove to exe folder, or (R)ebuild? [T/M/R]: ").strip().upper()
            
            if choice == 'T':
                print("🚀 Testing executable...")
                subprocess.Popen([str(best_match['path'])])
                return
            elif choice == 'M':
                target = Path(r"C:\Users\Bario\OneDrive\Dokumente\download\exe") / "BetterMint Modded Installer.exe"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(best_match['path'], target)
                print(f"✅ Copied to: {target}")
                return
    else:
        print("❌ No recent executables found")
    
    # No suitable executable found, build new one
    print("\n🔄 Building new executable...")
    
    if simple_build():
        # Verify the build
        expected_path = Path(r"C:\Users\Bario\OneDrive\Dokumente\download\exe\BetterMint Modded Installer.exe")
        if expected_path.exists():
            size_mb = expected_path.stat().st_size / (1024 * 1024)
            print(f"\n🎉 SUCCESS!")
            print(f"📁 Location: {expected_path}")
            print(f"📦 Size: {size_mb:.1f} MB")
            
            # Clean up
            for cleanup_dir in ["build", "dist"]:
                if Path(cleanup_dir).exists():
                    shutil.rmtree(cleanup_dir)
            
            # Test option
            test = input("\nTest the executable now? (y/n): ").strip().lower()
            if test.startswith('y'):
                subprocess.Popen([str(expected_path)])
        else:
            print("❌ Build reported success but executable not found")
            # Search again
            new_files = find_recent_executables()
            if new_files:
                latest = max(new_files, key=lambda x: x['created'])
                print(f"🔍 But found this recent file: {latest['path']}")

if __name__ == "__main__":
    main()
