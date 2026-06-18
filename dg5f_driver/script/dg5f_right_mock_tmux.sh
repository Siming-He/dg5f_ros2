#!/usr/bin/env bash
set -euo pipefail

SESSION="${DG5F_TMUX_SESSION:-dg5f_right_mock}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="${DG5F_WS_ROOT:-$(cd "$SCRIPT_DIR/../../../.." && pwd)}"
SETUP_FILE="$WS_ROOT/install/setup.bash"
SRC_ROOT="$WS_ROOT/src/dg5f_ros2"
VIS_LAUNCH="$SRC_ROOT/dg5f_description/launch/dg5f_right_live_display.launch.py"
PANEL="$SRC_ROOT/dg5f_driver/script/dg5f_right_control_panel.py"
STATUS="$SRC_ROOT/dg5f_driver/script/dg5f_right_status_watch.sh"
LOG_DIR="${ROS_LOG_DIR:-/tmp/dg5f_ros_logs}"

if [[ ! -f "$SETUP_FILE" ]]; then
  echo "Missing $SETUP_FILE. Build the workspace first: cd $WS_ROOT && colcon build"
  exit 1
fi

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux attach-session -t "$SESSION"
  exit 0
fi

mkdir -p "$LOG_DIR"

run_cmd() {
  printf 'cd %q; export ROS_LOG_DIR=%q; source %q; %s' "$WS_ROOT" "$LOG_DIR" "$SETUP_FILE" "$1"
}

tmux new-session -d -s "$SESSION" -n main "$(run_cmd 'ros2 launch dg5f_driver dg5f_right_mock.launch.py')"
tmux split-window -h -t "$SESSION:main" "$(run_cmd "sleep 2; ros2 launch $VIS_LAUNCH")"
tmux split-window -v -t "$SESSION:main.1" "$(run_cmd "sleep 2; python3 $PANEL --mode position")"
tmux split-window -v -t "$SESSION:main.0" "$(run_cmd "sleep 2; bash $STATUS")"
tmux select-pane -t "$SESSION:main.0" -T "mock controller"
tmux select-pane -t "$SESSION:main.1" -T "status"
tmux select-pane -t "$SESSION:main.2" -T "live rviz"
tmux select-pane -t "$SESSION:main.3" -T "joint target panel"
tmux select-layout -t "$SESSION:main" tiled
tmux attach-session -t "$SESSION"
