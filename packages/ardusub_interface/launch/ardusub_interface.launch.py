import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _home_from_world(world_name: str) -> str:
    home_lat = 33.810313
    home_lon = -118.393867
    home_alt = 0.0
    home_heading = 0.0

    if world_name == "empty.sdf":
        return f"{home_lat},{home_lon},{home_alt},{home_heading}"

    world_filename = f"{world_name}.world"
    resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    search_dirs = resource_path.split(":") if resource_path else []

    for directory in search_dirs:
        candidate = os.path.join(directory, world_filename)
        if not os.path.exists(candidate):
            continue

        try:
            tree = ET.parse(candidate)
            world_elem = tree.getroot().find("world")
            sc = world_elem.find("spherical_coordinates") if world_elem is not None else None
            if sc is None:
                break

            lat_elem = sc.find("latitude_deg")
            lon_elem = sc.find("longitude_deg")
            elev_elem = sc.find("elevation")
            head_elem = sc.find("heading_deg")

            if lat_elem is not None:
                home_lat = float(lat_elem.text)
            if lon_elem is not None:
                home_lon = float(lon_elem.text)
            if elev_elem is not None:
                home_alt = float(elev_elem.text)
            if head_elem is not None:
                home_heading = float(head_elem.text)
        except Exception as exc:
            print(f"World coordinate parsing failed: {exc}. Using default ArduSub home.")
        break

    return f"{home_lat},{home_lon},{home_alt},{home_heading}"


def launch_setup(context, *args, **kwargs):
    pkg_ardusub_interface = get_package_share_directory("ardusub_interface")

    ardusub_params_file = os.path.join(
        pkg_ardusub_interface, "config", "ardusub.parm"
    )
    mavros_params_file = os.path.join(
        pkg_ardusub_interface, "mavros_params", "sim_mavros_params.yaml"
    )

    launch_ardusub = LaunchConfiguration("ardusub")
    launch_mavros = LaunchConfiguration("mavros")
    use_sim_time = LaunchConfiguration("use_sim_time")
    odom_source = LaunchConfiguration("odom_source").perform(context)
    world_name = LaunchConfiguration("world_name").perform(context)
    home = LaunchConfiguration("home").perform(context)
    home_str = home if home else _home_from_world(world_name)

    ardusub_launch = ExecuteProcess(
        cmd=[
            "ardusub",
            "-S",
            "-w",
            "-M",
            "JSON",
            "--defaults",
            ardusub_params_file,
            "-I0",
            "--home",
            home_str,
        ],
        output="screen",
        condition=IfCondition(launch_ardusub),
    )

    mavros_node = Node(
        package="mavros",
        executable="mavros_node",
        output="screen",
        parameters=[mavros_params_file],
        condition=IfCondition(launch_mavros),
    )

    actions = [ardusub_launch, mavros_node]

    if odom_source == "ground_truth":
        actions.append(
            Node(
                package="ardusub_interface",
                executable="ground_truth_to_mavros",
                output="screen",
                parameters=[{"use_sim_time": use_sim_time}],
            )
        )
    elif odom_source not in ("none", "false"):
        raise ValueError(
            "odom_source must be one of: ground_truth, none"
        )

    return actions


def generate_launch_description():
    args = [
        DeclareLaunchArgument(
            "ardusub",
            default_value="true",
            description="Launch ArduSub SITL",
        ),
        DeclareLaunchArgument(
            "mavros",
            default_value="true",
            description="Launch MAVROS",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation time for interface adapter nodes",
        ),
        DeclareLaunchArgument(
            "world_name",
            default_value="empty.sdf",
            description="Gazebo world name used to derive ArduSub home coordinates",
        ),
        DeclareLaunchArgument(
            "home",
            default_value="",
            description="Optional ArduSub home override: lat,lon,alt,yaw",
        ),
        DeclareLaunchArgument(
            "odom_source",
            default_value="ground_truth",
            description="Odometry adapter to publish to /mavros/odometry/out: ground_truth or none",
        ),
    ]

    return LaunchDescription(args + [OpaqueFunction(function=launch_setup)])
