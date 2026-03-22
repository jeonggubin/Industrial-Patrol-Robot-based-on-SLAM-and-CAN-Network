import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    home_path = os.path.expanduser('~')
    ekf_config_path = os.path.join(home_path, 'ros2_ws', 'my_ekf.yaml')

    return LaunchDescription([
        # 1. IMU 정적 TF: 회전이 반대면 --yaw 값을 3.14159로 수정
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_pub_imu',
            arguments=[
                '--x', '0', '--y', '0', '--z', '0', 
                '--yaw', '3.14159', '--pitch', '0', '--roll', '0', # 180도 회전 반영
                '--frame-id', 'base_link', 
                '--child-frame-id', 'imu_link'
            ]
        ),

        # 2. 라이다 정적 TF: 전진 시 뒤로 가면 --yaw 값을 3.14159로 수정
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_tf_pub_laser',
            arguments=[
                '--x', '0.1', '--y', '0', '--z', '0.4', 
                '--yaw', '3.14159', '--pitch', '0', '--roll', '0', # 180도 회전 반영
                '--frame-id', 'base_link', 
                '--child-frame-id', 'base_scan'
            ]
        ),

        # 3. EKF 노드
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config_path]
        )
    ])