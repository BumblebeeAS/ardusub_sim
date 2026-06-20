cmake_minimum_required(VERSION 3.12.2)
project(bluerov_sim)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(dave_worlds REQUIRED)

# Install the bluerov_sim Python module so it is importable (`import bluerov_sim`).
ament_python_install_package(${PROJECT_NAME})

install(DIRECTORY launch config models urdf
  DESTINATION share/${PROJECT_NAME})

# dave_worlds installs its worlds under share/dave_worlds/worlds, but its own
# env hook only puts share/dave_worlds on GZ_SIM_RESOURCE_PATH. gz sim searches
# only the top level of each resource-path root, so a bare world name in that
# subdir (e.g. world_name:=dave_ocean_waves) isn't found. Add the worlds subdir
# to GZ_SIM_RESOURCE_PATH here so it resolves by name, without the launch file
# having to resolve world paths itself.
get_filename_component(_dave_worlds_share "${dave_worlds_DIR}/.." ABSOLUTE)
set(DAVE_WORLDS_WORLDS_DIR "${_dave_worlds_share}/worlds")

ament_environment_hooks(hooks/setup.dsv)
ament_environment_hooks(hooks/dave_worlds_path.dsv.in)

ament_package()
