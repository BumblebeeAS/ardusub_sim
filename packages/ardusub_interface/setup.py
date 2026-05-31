from glob import glob

from setuptools import find_packages, setup

package_name = "ardusub_interface"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
        (f"share/{package_name}/mavros_params", glob("mavros_params/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="maintainer",
    maintainer_email="maintainer@example.com",
    description="ArduSub SITL and MAVROS interface for BlueROV-style simulations",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "ground_truth_to_mavros = ardusub_interface.ground_truth_to_mavros:main",
            "dvl_to_mavros = ardusub_interface.dvl_to_mavros:main",
        ],
    },
)
