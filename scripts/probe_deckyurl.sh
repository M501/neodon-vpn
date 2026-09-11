#!/bin/bash
# One-shot: verify Decky official installer URL resolves to a script.
curl -sL -m 40 -o /tmp/decky-inst.sh -w "HTTP:%{http_code} SIZE:%{size_download}\n" https://github.com/SteamDeckHomebrew/decky-installer/releases/latest/download/install_release.sh
head -n 3 /tmp/decky-inst.sh 2>/dev/null
