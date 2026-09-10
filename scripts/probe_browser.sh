#!/bin/bash
# One-shot: real browser engine (Firefox headless) fetch of store API, timed.
time flatpak run --branch=stable --arch=x86_64 org.mozilla.firefox --headless --screenshot /tmp/db.png "https://plugins.deckbrew.xyz/plugins?per_page=1" 2>&1 | tail -n 3
ls -la /tmp/db.png 2>/dev/null
