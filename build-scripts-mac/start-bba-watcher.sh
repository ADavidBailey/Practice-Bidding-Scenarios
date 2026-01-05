#!/bin/bash
# Start the BBA Watcher on the Windows VM
# This runs it detached so SSH can exit immediately

ssh rick@10.211.55.5 "powershell -Command \"Start-Process powershell -ArgumentList '-WindowStyle Minimized -File P:\build-scripts\BBAWatcher.ps1'\""
echo "BBA Watcher started on Windows VM"
