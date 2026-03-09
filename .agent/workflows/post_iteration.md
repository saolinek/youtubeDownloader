---
description: Post-iteration deployment
---
When the user asks you to implement a feature, fix a bug, or perform an iteration on the YTMusic Smart Downloader application, you MUST ALWAYS perform this post-iteration workflow once the coding is complete:

1. Clean the previous build:
```bash
rm -rf build dist
```

// turbo
2. Run the py2app setup script within the virtual environment to build the application bundle:
```bash
source venv/bin/activate && python3 setup_app.py py2app
```

// turbo
3. Move or copy the built `.app` to the macOS Applications folder:
```bash
cp -R dist/"YTMusic Smart Downloader.app" /Applications/
```

4. Notify the user that the new version has been deployed to the Applications folder and is ready to use.
