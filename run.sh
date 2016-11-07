#!/usr/bin/env bash
RUN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
"$RUN_DIR/run.py" -c "$RUN_DIR/config.json" >> "$RUN_DIR/run.log"