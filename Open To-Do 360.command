#!/bin/bash
# Double-click to start To-Do 360. Close this window to stop it.
cd "$(dirname "$0")" || exit 1
exec /usr/bin/env python3 app/server.py
