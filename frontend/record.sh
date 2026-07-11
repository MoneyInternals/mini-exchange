#!/usr/bin/env bash
# Opens the terminal UI in a chromeless Chrome window at recording size (2560x1440).
open -na "Google Chrome" --args \
  --app="file://$(cd "$(dirname "$0")" && pwd)/order-book-terminal.html" \
  --user-data-dir="$HOME/.mi-recording-profile" \
  --window-size=2560,1440