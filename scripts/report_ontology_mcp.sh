#!/bin/sh
# Starts the report-ontology MCP server for the plugin.
# Uses $REPORT_ONTOLOGY_HOME when it is set (a checkout of Cynergis/report-ontology); otherwise keeps a
# clone in the user's cache and updates it, so nothing has to be exported in a shell profile (VS Code
# started from the Dock does not read one).
set -e
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "report-ontology MCP server: uv is not on the PATH; install it (https://docs.astral.sh/uv/) or set REPORT_ONTOLOGY_HOME and uv's location" >&2
  exit 1
fi
HOME_DIR="${REPORT_ONTOLOGY_HOME:-}"
if [ -z "$HOME_DIR" ]; then
  HOME_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/pdf-to-template/report-ontology"
  if [ ! -d "$HOME_DIR/.git" ]; then
    mkdir -p "$(dirname "$HOME_DIR")"
    git clone -q --depth 1 https://github.com/Cynergis/report-ontology "$HOME_DIR" >&2
  else
    git -C "$HOME_DIR" pull -q --ff-only >&2 || true
  fi
fi
exec uv run --no-project --with-requirements "$HOME_DIR/requirements.txt" python "$HOME_DIR/tools/mcp_server.py"
