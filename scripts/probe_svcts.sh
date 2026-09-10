#!/bin/bash
# One-shot: verify systemd timestamp format parses with our strptime.
U=$(systemctl --user list-units --type=service --state=running --no-legend 2>/dev/null | head -n 1 | awk '{print $1}')
echo "UNIT=$U"
TS=$(systemctl --user show "$U" -p ActiveEnterTimestamp --value)
echo "TS=$TS"
python3 -c "import datetime,sys; print(int(datetime.datetime.strptime(sys.argv[1], '%a %Y-%m-%d %H:%M:%S %z').timestamp()))" "$TS"
