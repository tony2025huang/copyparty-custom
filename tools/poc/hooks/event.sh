#!/bin/sh
printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> /root/.openclaw/workspace/.tmp/openclaw-spikes/copyparty/results/hook-events.log
