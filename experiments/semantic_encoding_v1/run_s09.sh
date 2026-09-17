#!/bin/sh
# Local demo launcher. Reads credentials only through run_s09_live.py.
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_dir"
s09_python=${S09_PYTHON:-python3}
if ! "$s09_python" -c 'import openai; from importlib.metadata import version; version("openai")' >/dev/null 2>&1; then
    s09_dependencies=${S09_DEPENDENCIES:-/private/tmp/symbolicrca-featherless-sdk}
    PYTHONPATH="$s09_dependencies${PYTHONPATH:+:$PYTHONPATH}"
    export PYTHONPATH
    if ! "$s09_python" -c 'import openai; from importlib.metadata import version; version("openai")' >/dev/null 2>&1; then
        printf '%s\n' 'OpenAI SDK unavailable. Set S09_PYTHON to a Python environment with openai installed, or S09_DEPENDENCIES to its package directory.' >&2
        exit 2
    fi
fi
s09_run_id="s09-manual-$(date -u +%Y%m%dT%H%M%SZ)-$$"
s09_exit=0
"$s09_python" -m experiments.semantic_encoding_v1.run_s09_live --run-id "$s09_run_id" "$@" || s09_exit=$?
printf '\nResults: %s/data/experiments/semantic-encoding-v1/S09/%s/\n' "$repo_dir" "$s09_run_id"
exit "$s09_exit"
