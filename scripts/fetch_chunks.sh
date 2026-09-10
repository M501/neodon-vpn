#!/bin/bash
# One-shot: fetch loader frontend chunks, find plugin factory invocation.
cd /tmp
for c in chunk-BQQVI2v2.js chunk-C53CtY1F.js chunk-BFRQAfGY.js chunk-B1E4s6v6.js; do
  curl -s -m 20 "http://127.0.0.1:1337/frontend/$c" -o "/tmp/dc-$c" 2>/dev/null
done
ls -la /tmp/dc-*.js
grep -l "callPluginMethod" /tmp/dc-*.js
