"""
Cross-platform desktop notifications.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess


def _send_macos_notification(title: str, message: str) -> bool:
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')
    subprocess.run(
        ["osascript", "-e", f'display notification "{safe_message}" with title "{safe_title}"'],
        capture_output=True,
        timeout=5,
        check=False,
    )
    return True


def _send_windows_notification(title: str, message: str) -> bool:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return False

    env = os.environ.copy()
    env["YTM_TITLE"] = title
    env["YTM_MESSAGE"] = message
    script = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = $env:YTM_TITLE
$notify.BalloonTipText = $env:YTM_MESSAGE
$notify.Visible = $true
$notify.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$notify.Dispose()
"""
    subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        env=env,
        capture_output=True,
        timeout=10,
        check=False,
    )
    return True


def _send_linux_notification(title: str, message: str) -> bool:
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return False

    subprocess.run(
        [notify_send, title, message],
        capture_output=True,
        timeout=5,
        check=False,
    )
    return True


def send_notification(title: str, message: str) -> bool:
    """Best-effort desktop notification."""
    system = platform.system()

    try:
        if system == "Darwin":
            return _send_macos_notification(title, message)
        if system == "Windows":
            return _send_windows_notification(title, message)
        return _send_linux_notification(title, message)
    except Exception:
        return False
