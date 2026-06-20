# ArduSub Simulation

ArduSub + Gazebo simulation for [BlueROV](https://bluerobotics.com/store/rov/bluerov2/).

## Clone the Repo

Clone this repo into `~/workspaces/bluerov_ws/src`. If you prefer to place it in another location, edit the paths below.

## Get the Dependencies

Install `vcstool` (add the ROS 2 apt repository first, [example](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html#setup-sources)):

```bash
sudo apt-get update
sudo apt-get install python3-vcstool
```

Then get the dependencies:

```bash
cd ~/workspaces/bluerov_ws
vcs import src < src/ardusub_sim/dependencies.repos
```

## Build the Image

```bash
cd ~/workspaces/bluerov_ws/src/ardusub_sim
./build.bash
```

This creates `ardusub_sim:humble`.

## Start the Container

Install `rocker`: https://github.com/osrf/rocker#installation

Then start the container:

```bash
rocker --devices /dev/dri --x11 --network=host --ipc=host \
  --volume ~/workspaces/bluerov_ws:/root/HOST/bluerov_ws -- \
  ardusub_sim:humble
```

## Build the ROS Packages

Inside the container:

```bash
cd /root/HOST/bluerov_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to ardusub_interface bluerov_sim
```

## Run the Sim

```bash
source install/setup.bash
ros2 launch bluerov_sim bluerov_sim.launch.py \
  world_name:=dave_ocean_waves \
  ardusub:=true \
  mavros:=true \
  gui:=true
```

## Simple Commands

In a second shell inside the same container:

```bash
rocker --devices /dev/dri --x11 --network=host --ipc=host \
  --volume ~/workspaces/bluerov_ws:/root/HOST/bluerov_ws -- \
  ardusub_sim:humble

cd /root/HOST/bluerov_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
```

Check that MAVROS and Gazebo data are flowing:

```bash
ros2 topic echo /mavros/state --once
ros2 topic echo /mavros/local_position/pose --once
ros2 topic hz /bluerov/odom
```

Arm and switch to GUIDED:

```bash
ros2 service call /mavros/cmd/arming mavros_msgs/srv/CommandBool "{value: true}"
ros2 service call /mavros/set_mode mavros_msgs/srv/SetMode "{custom_mode: 'GUIDED'}"
```

Send one position setpoint:

```bash
ros2 topic pub --once /mavros/setpoint_position/local geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0, z: -1.0}, orientation: {w: 1.0}}}"
```

Useful launch switches:

```bash
odom_source:=ground_truth   # default
odom_source:=none           # no odometry adapter
```

## Architecture

The simulation command and feedback loop is:

```text
ROS command
→ MAVROS
→ ArduSub SITL
→ ArduPilot Gazebo plugin
→ Gazebo physics
→ odometry adapter
→ MAVROS and TF
```

## Notes

- Map poses use ENU; depth below the surface has negative z.
- Host networking is required for the default MAVLink ports.
- If MAVROS is disconnected, check that ArduSub and the Gazebo bridge started.
- If local position is not updating, check the selected odometry adapter.
