#!/usr/bin/env bash
RUN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )";
"$RUN_DIR/run.py" >> "$RUN_DIR/run.log"