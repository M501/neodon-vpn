#!/bin/bash
# Fetch v2RayTun preset icons once; GUI falls back to emoji/letter offline.
D=~/AI/neodon-vpn/icons
mkdir -p "$D"
dl() { [ -s "$D/$1" ] || curl -s -m 15 -o "$D/$1" "$2" && echo "OK $1 $(stat -c %s "$D/$1" 2>/dev/null)"; }
dl ru-bez-vpn.jpg https://storage.yandexcloud.net/v2raytun/icons/2025/10/25488ea5-c0c1-4336-b9c4-0d7fd52c4d63.jpg
dl popular-ai.png https://storage.yandexcloud.net/v2raytun/icons/2025/10/1d3a4928-75ed-473e-9fce-87a268b2839b.png
dl social-networks.png https://storage.yandexcloud.net/v2raytun/icons/2025/10/e7a66419-f3ac-4533-b7a8-a5ffa9cd7769.png
dl only-unavailable.png https://storage.yandexcloud.net/v2raytun/icons/2025/10/b7059b6b-f9ee-492a-afb6-c29e58a96846.png
dl ru-traffic-direct.png https://storage.yandexcloud.net/v2raytun/icons/2025/10/a272cfb4-51b6-46f3-969d-45c70d18b64e.png
dl socseti-vpn.jpg https://storage.yandexcloud.net/v2raytun/icons/2025/09/e0c34fa1-6b7a-408d-8a35-073610538807.jpg
dl basic-set.png https://storage.yandexcloud.net/v2raytun/icons/2025/09/a3b361ed-e0cf-4c18-9c00-41a5976115d1.png
dl russia-mimo.png https://storage.yandexcloud.net/v2raytun/icons/2025/09/b71d69e6-8e75-445d-81ce-cd8323b128dd.png
echo DONE
