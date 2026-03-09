Windows build files live here.

The actual executable is generated as `distr/YTMusic Smart Downloader.exe` by:

- running `build_windows.ps1` on Windows
- or pushing to `main`, which triggers the GitHub Actions workflow in `.github/workflows/build-windows.yml`

This repo builds the Windows executable on a Windows runner because PyInstaller does not reliably cross-compile a Windows `.exe` from macOS.
