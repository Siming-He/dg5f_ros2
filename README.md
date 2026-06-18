# DG5F ROS 2

[![CI](https://github.com/tesollodelto/dg5f_ros2/actions/workflows/ci.yml/badge.svg)](https://github.com/tesollodelto/dg5f_ros2/actions/workflows/ci.yml)
![ROS 2 Humble](https://img.shields.io/badge/ROS_2-Humble-blue?logo=ros)
![ROS 2 Jazzy](https://img.shields.io/badge/ROS_2-Jazzy-blue?logo=ros)

ROS 2 packages for the **Delto Gripper DG5F** (5-finger robotic hand, left/right).

## Packages

| Package | Description |
|---|---|
| `dg5f_description` | URDF/xacro model, meshes, and RViz display launch |
| `dg5f_driver` | ros2_control hardware driver and controller launch files |
| `dg5f_gz` | Gazebo simulation |
| `dg5f_moveit_config` | MoveIt 2 configuration (SRDF, planners, mock hardware) |

## New Laptop Setup

Use a normal ROS 2 workspace with this repository checked out as
`src/dg5f_ros2`, plus the two TESOLLO dependency repositories next to it.

```bash
mkdir -p ~/manipulation_ws/src
cd ~/manipulation_ws/src

git clone git@github.com:Siming-He/force_control.git dg5f_ros2
git clone https://github.com/tesollodelto/dg_hardware.git
git clone https://github.com/tesollodelto/dg_tcp_comm.git

cd ~/manipulation_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

If you open a new terminal later, run:

```bash
cd ~/manipulation_ws
source install/setup.bash
```

Install `tmux` if you want the one-command right-hand workflows:

```bash
sudo apt update
sudo apt install -y tmux
```

## Dependencies

This repository requires the following packages to build:

```bash
# Clone into your ROS 2 workspace src directory
git clone https://github.com/tesollodelto/dg_hardware.git
git clone https://github.com/tesollodelto/dg_tcp_comm.git
```

- [`delto_hardware`](https://github.com/tesollodelto/dg_hardware) — Unified hardware interface for Delto grippers
- [`delto_tcp_comm`](https://github.com/tesollodelto/dg_tcp_comm) — TCP communication library for Delto grippers

## Build

```bash
cd ~/manipulation_ws
colcon build --symlink-install
source install/setup.bash
```

For a smaller rebuild while developing the driver:

```bash
colcon build --symlink-install --packages-select dg5f_driver dg5f_description
source install/setup.bash
```

## Quick Control Matrix

The right-hand namespace is `/dg5f_right`. Replace `169.254.186.72` with the
actual DG5F IP address on your robot network.

| Mode | One-command helper | Direct launch |
|---|---|---|
| Mock position | `ros2 run dg5f_driver dg5f_right_mock_tmux.sh` | `ros2 launch dg5f_driver dg5f_right_mock.launch.py` |
| Mock effort | `ros2 run dg5f_driver dg5f_right_mock_effort_tmux.sh` | `ros2 launch dg5f_driver dg5f_right_mock_effort.launch.py` |
| Real position | `ros2 run dg5f_driver dg5f_right_real_tmux.sh 169.254.186.72` | `ros2 launch dg5f_driver dg5f_right_driver.launch.py delto_ip:=169.254.186.72 delto_port:=502` |
| Real effort | `ros2 run dg5f_driver dg5f_right_effort_tmux.sh 169.254.186.72` | `ros2 launch dg5f_driver dg5f_right_effort_controller.launch.py delto_ip:=169.254.186.72 delto_port:=502` |

The tmux helpers open four panes: the controller, a status watcher, RViz, and a
small GUI control panel. Re-running a helper attaches to the existing session.
Exit a helper session with `tmux kill-session -t <session-name>` or close the
panes manually.

Common session names:

```bash
tmux kill-session -t dg5f_right_mock
tmux kill-session -t dg5f_right_mock_effort
tmux kill-session -t dg5f_right_real
tmux kill-session -t dg5f_right_effort
```

### Real Robot Network Check

Before launching real hardware, put the DG5F in Developer Mode, connect the
Ethernet link, set your laptop interface on the same subnet, and verify the IP:

```bash
ping 169.254.186.72
```

### Fingertip Sensor Topics

For real hardware, the fingertip sensors require both hardware reading and ROS
broadcasters:

```bash
FINGERTIP_SENSOR=true FT_BROADCASTER=true IO=true \
ros2 run dg5f_driver dg5f_right_effort_tmux.sh 169.254.186.72
```

The equivalent direct launch arguments are:

```bash
ros2 launch dg5f_driver dg5f_right_effort_controller.launch.py \
  delto_ip:=169.254.186.72 \
  fingertip_sensor:=true \
  ft_broadcaster:=true \
  io:=true
```

## Launch Reference

```bash
# RViz display
ros2 launch dg5f_description dg5f_right_display.launch.py
ros2 launch dg5f_description dg5f_left_display.launch.py

# Hardware driver
ros2 launch dg5f_driver dg5f_right_driver.launch.py
ros2 launch dg5f_driver dg5f_left_driver.launch.py

# Effort controller
ros2 launch dg5f_driver dg5f_right_effort_controller.launch.py
ros2 launch dg5f_driver dg5f_left_effort_controller.launch.py

# PID controller (20 individual controllers, one per joint)
ros2 launch dg5f_driver dg5f_right_pid_controller.launch.py
ros2 launch dg5f_driver dg5f_left_pid_controller.launch.py

# PID all controller (single multi-joint controller)
ros2 launch dg5f_driver dg5f_right_pid_all_controller.launch.py
ros2 launch dg5f_driver dg5f_left_pid_all_controller.launch.py
ros2 launch dg5f_driver dg5f_both_pid_all_controller.launch.py

# Gazebo simulation
ros2 launch dg5f_gz dg5f_right_gz.launch.py
ros2 launch dg5f_gz dg5f_left_gz.launch.py
ros2 launch dg5f_gz dg5f_both_gz.launch.py

# Mock hardware (no device required)
ros2 launch dg5f_driver dg5f_right_mock.launch.py
ros2 launch dg5f_driver dg5f_left_mock.launch.py

# Mock effort control (no device required)
ros2 launch dg5f_driver dg5f_right_mock_effort.launch.py
ros2 launch dg5f_driver dg5f_left_mock_effort.launch.py

# MoveIt (mock hardware, default)
ros2 launch dg5f_moveit_config dg5f_right_moveit.launch.py
ros2 launch dg5f_moveit_config dg5f_left_moveit.launch.py

# MoveIt (real hardware)
ros2 launch dg5f_moveit_config dg5f_right_moveit.launch.py use_mock:=false delto_ip:=169.254.186.72
```
