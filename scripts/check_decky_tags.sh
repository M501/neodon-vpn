#!/bin/bash
# One-shot: Decky tags from releases page HTML (api filtered).
curl -sL -m 30 https://github.com/SteamDeckHomebrew/decky-loader/releases 2>/dev/null \
  | grep -oE '/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+' | sort -uV | tail -n 5
