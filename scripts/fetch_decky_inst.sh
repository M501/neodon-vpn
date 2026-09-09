#!/bin/bash
# One-shot: download Decky installer release script.
curl -sL -m 60 -o /tmp/decky-install.sh https://github.com/SteamDeckHomebrew/decky-installer/releases/latest/download/install_release.sh 2>&1
ls -la /tmp/decky-install.sh 2>/dev/null
head -n 5 /tmp/decky-install.sh 2>/dev/null
