#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: ros2 run dg5f_driver dg5f_right_status_watch.sh [DELTO_IP]"
  exit 0
fi

DELTO_IP="${1:-${DELTO_IP:-}}"
NS="${DG5F_NAMESPACE:-dg5f_right}"
MANAGER="/$NS/controller_manager"
JOINT_STATES="/$NS/joint_states"

while true; do
  clear 2>/dev/null || true
  echo "DG5F right status"
  echo "================="
  date
  echo

  if [[ -n "$DELTO_IP" ]]; then
    if ping -c 1 -W 1 "$DELTO_IP" >/dev/null 2>&1; then
      echo "IP $DELTO_IP: reachable"
    else
      echo "IP $DELTO_IP: NOT reachable"
    fi
  else
    echo "IP: not set"
  fi

  echo
  echo "Controller manager:"
  if timeout 2s ros2 service list 2>/dev/null | grep -qx "$MANAGER/list_controllers"; then
    if ! timeout 3s ros2 control list_controllers -c "$MANAGER" 2>/dev/null; then
      echo "  $MANAGER exists, but list_controllers did not return"
    fi
  else
    echo "  not available at $MANAGER"
  fi

  echo
  echo "Joint states:"
  if timeout 2s ros2 topic list 2>/dev/null | grep -qx "$JOINT_STATES"; then
    if timeout 2s ros2 topic echo --once "$JOINT_STATES" --field name >/tmp/dg5f_joint_names.txt 2>/dev/null; then
      joint_count="$(grep -c "rj_dg_" /tmp/dg5f_joint_names.txt || true)"
      echo "  $JOINT_STATES is publishing ($joint_count DG5F joints seen)"
    else
      echo "  topic exists, but no message arrived within 2 seconds"
    fi
  else
    echo "  topic is missing: $JOINT_STATES"
  fi

  echo
  echo "RViz needs robot_description plus joint states for all moving finger links."
  echo "If controller_manager and joint_states are missing, check robot power/IP/network."
  sleep 2
done
