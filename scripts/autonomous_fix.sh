#!/bin/bash
# Simple autonomous fixing - delegates to full startup
# Usage: ./scripts/autonomous_fix.sh config/money-making-app.yaml

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/autonomous_fix_with_redis.sh" "$@"
