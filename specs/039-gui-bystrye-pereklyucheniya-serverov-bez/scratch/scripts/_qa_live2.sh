#!/bin/bash
# Re-run the live QA matrix detached (systemd-run) so an SSH hiccup cannot kill it.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
QA=/home/m26/AI/neodon-qa
LIVE=/home/m26/AI/neodon-vpn/neodon-vpn.py

# newest fixed live-case scripts into the snapshot
for f in l3_failures.sh l3_perf.sh; do
  [ -f "/home/m26/qa_patch/$f" ] && cp "/home/m26/qa_patch/$f" "$QA/qa/live/$f"
done
rm -rf "$QA/qa-results"

cat > /home/m26/qa_live_run.sh <<'RUN'
#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0 DISPLAY=:0 QT_QPA_PLATFORMTHEME=kde
export NEODON_REPO=/home/m26/AI/neodon-qa
export NEODON_APP=/home/m26/AI/neodon-vpn/neodon-vpn.py
export NEODON_BACKEND=/home/m26/AI/singbox
export NEODON_LIVE=1 NEODON_ALLOW_DISRUPTIVE=1 NEODON_ALLOW_FIREWALL=1 NEODON_ALLOW_UI_INPUT=1
export NEODON_WORKING_SERVER=0
cd /home/m26/AI/neodon-qa || exit 1
bash /home/m26/AI/neodon-qa/qa/run-all.sh --live
echo "LIVE_MATRIX_RC=$?"
RUN
chmod +x /home/m26/qa_live_run.sh

systemctl --user reset-failed neodon-qa-live.service 2>/dev/null
systemd-run --user --unit=neodon-qa-live --collect \
  --setenv=XDG_RUNTIME_DIR=/run/user/1000 \
  --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  bash -c 'bash /home/m26/qa_live_run.sh > /home/m26/qa_live2.log 2>&1'
sleep 2
echo "unit: $(systemctl --user is-active neodon-qa-live.service)"
echo "log started: $(ls -la /home/m26/qa_live2.log 2>/dev/null)"
