FROM ros:humble-ros-base-jammy

SHELL ["/bin/bash", "-o", "pipefail", "-o", "errexit", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    echo $TZ > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

# System dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

# Setup Gazebo/OSRF repository
RUN curl https://packages.osrfoundation.org/gazebo.gpg \
        --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
        http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
        | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    gz-harmonic \
    libgl1 \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgz-sim8-dev \
    libopencv-dev \
    libyaml-cpp-dev \
    pkg-config \
    python3-empy \
    python3-colcon-common-extensions \
    python3-setuptools \
    rapidjson-dev \
    ros-humble-mavros \
    ros-humble-mavros-extras \
    ros-humble-ros-gzharmonic \
    ros-humble-sdformat-urdf \
    ros-humble-tf-transformations \
    wget && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8

# GeographicLib datasets (required by MAVROS)
# Source: https://docs.ros.org/en/humble/p/mavros/#binary-installation-deb
RUN apt-get update && apt-get install -y --no-install-recommends geographiclib-tools && \
    . /opt/ros/humble/setup.sh && \
    ros2 run mavros install_geographiclib_datasets.sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ArduSub SITL
ARG HOME_DIR=/root
ARG ARDUSUB_DIR=${HOME_DIR}/auv
ARG ARDUSUB_FIRMWARE_URL=https://firmware.ardupilot.org/Sub/stable/sitl/ardusub

WORKDIR ${ARDUSUB_DIR}
RUN mkdir -p /opt/ardupilot/bin && \
    wget -q -O /opt/ardupilot/bin/ardusub ${ARDUSUB_FIRMWARE_URL} && \
    chmod +x /opt/ardupilot/bin/ardusub

ENV GZ_VERSION=harmonic
ENV PATH="/opt/ardupilot/bin:/root/.local/bin:${PATH}"

WORKDIR ${HOME_DIR}
