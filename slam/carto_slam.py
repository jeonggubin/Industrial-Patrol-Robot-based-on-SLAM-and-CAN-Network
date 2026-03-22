import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    home_path = os.path.expanduser('~')
    carto_config_dir = os.path.join(home_path, 'ros2_ws')
    carto_config_basename = 'my_carto.lua'

    return LaunchDescription([
        # 1. Cartographer 메인 노드
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=[
                '-configuration_directory', carto_config_dir,
                '-configuration_basename', carto_config_basename
            ],
            remappings=[
                ('scan', '/scan'),
                ('imu', '/imu/mpu6050'),
                ('odom', '/odometry/filtered')
            ]
        ),

        # 2. RViz 시각화를 위한 지도 생성 노드
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=['-resolution', '0.05', '-publish_period_sec', '1.0']
        ),
    ])
