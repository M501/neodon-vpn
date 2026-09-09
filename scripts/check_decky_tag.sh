#!/bin/bash
# One-shot: resolve latest Decky tag via github.com redirect (api is filtered).
curl -sIL -m 30 -o /dev/null -w "%{url_effective}\n" https://github.com/SteamDeckHomebrew/decky-loader/releases/latest 2>&1
