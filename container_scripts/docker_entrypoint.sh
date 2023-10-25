#!/bin/bash

mkdir -p /seafile/server/logs

for LOG_FILE in ccnet.log controller.log notification-server.log onlyoffice.log seafdav.log seafile-monitor.log seafile.log seahub.log
do
  touch /seafile/server/logs/$LOG_FILE
  tail -F /seafile/server/logs/$LOG_FILE | sed -u "s/^/$LOG_FILE\ \|\ /g" &
done


exec python3 -u /seafile/setup_script.py
