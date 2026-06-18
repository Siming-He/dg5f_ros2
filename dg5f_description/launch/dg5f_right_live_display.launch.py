from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    share_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rviz_config_file = os.path.join(
        share_dir, "config", "dg5f_right_live_display.rviz"
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="dg5f_right_live_rviz",
        arguments=["-d", rviz_config_file],
        output="screen",
    )

    return LaunchDescription([rviz_node])
