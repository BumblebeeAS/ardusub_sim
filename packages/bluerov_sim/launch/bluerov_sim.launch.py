import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):

    pkg_bluerov_sim = get_package_share_directory("bluerov_sim")

    # Load URDF for robot_state_publisher.
    # The Gazebo SDF model (for physics/collisions/sensors) is loaded separately via model_sdf_path.
    urdf_path_str = LaunchConfiguration("urdf_path").perform(context)
    with open(urdf_path_str, "r") as f:
        robot_description = f.read()

    bluerov_gz_bridge_config_file = os.path.join(
        pkg_bluerov_sim, "config", "bluerov_gz_bridge.yaml"
    )

    paused = LaunchConfiguration("paused")
    gui = LaunchConfiguration("gui")
    use_sim_time = LaunchConfiguration("use_sim_time")
    debug = LaunchConfiguration("debug")
    headless = LaunchConfiguration("headless")
    verbose = LaunchConfiguration("verbose")
    namespace = LaunchConfiguration("namespace")
    world_name = LaunchConfiguration("world_name")
    launch_ardusub = LaunchConfiguration("ardusub")
    launch_mavros = LaunchConfiguration("mavros")
    odom_source = LaunchConfiguration("odom_source")
    nvidia_offload = LaunchConfiguration("nvidia_offload")

    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    roll = LaunchConfiguration("roll")
    pitch = LaunchConfiguration("pitch")
    yaw = LaunchConfiguration("yaw")

    # World files are provided by bb_worlds (via GZ_SIM_RESOURCE_PATH colcon hook)
    # and bluerov2_gz. Pass the filename directly; Gazebo resolves via the resource path.
    if world_name.perform(context) != "empty.sdf":
        w_name = world_name.perform(context)
        world_filename = f"{w_name}.world"
        gz_args = world_filename
    else:
        world_filename = None
        gz_args = world_name.perform(context)

    if headless.perform(context) == "true":
        gz_args += " -s"
    if paused.perform(context) == "false":
        gz_args += " -r"
    if debug.perform(context) == "true":
        gz_args += f" -v {verbose.perform(context)}"

    ardusub_interface_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("ardusub_interface"),
                        "launch",
                        "ardusub_interface.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments=[
            ("ardusub", launch_ardusub),
            ("mavros", launch_mavros),
            ("use_sim_time", use_sim_time),
            ("world_name", world_name),
            ("odom_source", odom_source),
        ],
    )

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("ros_gz_sim"),
                        "launch",
                        "gz_sim.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments=[
            ("gz_args", gz_args),
        ],
        condition=IfCondition(gui),
    )

    description_file = LaunchConfiguration("model_sdf_path")

    gz_spawner = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name",
            namespace,
            "-file",
            description_file,
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            roll,
            "-P",
            pitch,
            "-Y",
            yaw,
        ],
        output="both",
        condition=IfCondition(gui),
        parameters=[{"use_sim_time": use_sim_time}],
    )

    spawn_exit_handler = RegisterEventHandler(
        OnProcessExit(
            target_action=gz_spawner,
            on_exit=LogInfo(msg="Robot Model Spawn Process Finished"),
        )
    )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_clock_bridge",
        parameters=[{"config_file": bluerov_gz_bridge_config_file}],
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    # NVIDIA PRIME render offload: force gz sim's OpenGL rendering (ogre2 +
    # camera sensors) onto the discrete NVIDIA GPU via GLVND, instead of the
    # integrated GPU or Mesa software rasterizer (llvmpipe) — software rendering
    # tanks RTF. Set before the gz_sim include so the gz server process inherits
    # them. Disable with nvidia_offload:=false on Intel-only / non-NVIDIA hosts.
    offload_env = [
        SetEnvironmentVariable(
            "__NV_PRIME_RENDER_OFFLOAD",
            "1",
            condition=IfCondition(nvidia_offload),
        ),
        SetEnvironmentVariable(
            "__GLX_VENDOR_LIBRARY_NAME",
            "nvidia",
            condition=IfCondition(nvidia_offload),
        ),
    ]

    result = offload_env + [
        ardusub_interface_launch,
        gz_sim_launch,
        gz_spawner,
        spawn_exit_handler,
        gz_bridge,
        robot_state_publisher_node,
    ]

    return result


def generate_launch_description():
    args = [
        DeclareLaunchArgument(
            "nvidia_offload",
            default_value="true",
            description="Render gz sim on the discrete NVIDIA GPU via PRIME "
            "offload (set false on non-NVIDIA hosts)",
        ),
        DeclareLaunchArgument(
            "paused",
            default_value="true",
            description="Start the simulation paused",
        ),
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Flag to enable the gazebo gui",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Flag to indicate whether to use simulation time",
        ),
        DeclareLaunchArgument(
            "debug",
            default_value="false",
            description="Flag to enable the gazebo debug flag",
        ),
        DeclareLaunchArgument(
            "headless",
            default_value="false",
            description="Flag to enable the gazebo headless mode",
        ),
        DeclareLaunchArgument(
            "verbose",
            default_value="0",
            description="Adjust level of console verbosity",
        ),
        DeclareLaunchArgument(
            "world_name",
            default_value="empty.sdf",
            description="Gazebo world file to launch (resolved via GZ_SIM_RESOURCE_PATH)",
        ),
        DeclareLaunchArgument(
            "namespace",
            default_value="bluerov",
            description="Namespace",
        ),
        DeclareLaunchArgument(
            "x",
            default_value="0.0",
            description="Initial x position",
        ),
        DeclareLaunchArgument(
            "y",
            default_value="0.0",
            description="Initial y position",
        ),
        DeclareLaunchArgument(
            "z",
            default_value="0.0",
            description="Initial z position",
        ),
        DeclareLaunchArgument(
            "roll",
            default_value="0.0",
            description="Initial roll angle",
        ),
        DeclareLaunchArgument(
            "pitch",
            default_value="0.0",
            description="Initial pitch angle",
        ),
        DeclareLaunchArgument(
            "yaw",
            default_value="0.0",
            description="Initial yaw angle",
        ),
        DeclareLaunchArgument(
            "ardusub", default_value="true", description="Launch ArduSUB?"
        ),
        DeclareLaunchArgument(
            "mavros", default_value="true", description="Launch mavros?"
        ),
        DeclareLaunchArgument(
            "odom_source",
            default_value="ground_truth",
            description="Odometry adapter for ArduSub/MAVROS: ground_truth or none",
        ),
        DeclareLaunchArgument(
            "urdf_path",
            default_value=PathJoinSubstitution(
                [FindPackageShare("bluerov_sim"), "urdf", "bluerov2.urdf"]
            ),
            description="Path to URDF for robot_state_publisher",
        ),
        DeclareLaunchArgument(
            "model_sdf_path",
            default_value=PathJoinSubstitution(
                [FindPackageShare("bluerov_sim"), "models", "bluerov2", "model.sdf"]
            ),
            description="Path to SDF model for Gazebo spawning (physics, collisions, sensors)",
        ),
    ]

    return LaunchDescription(args + [OpaqueFunction(function=launch_setup)])
