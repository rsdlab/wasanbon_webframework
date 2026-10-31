# Wasanbon-Webframework

`wasanbon-webframework` is an webframework and a wrapper for [wasanbon](https://github.com/wasanbon/wasanbon).

`wasanbon` is a webframework for Robotic Software Developers with Robotic Technology Middleware (RT-middleware).

Robotic Technology Middleware is a standard for Robotic Softwares. In RTM, each software element (like actuator, sensor, algorithm, and so on) is regarded as Robotic Technology Component (RTC). Using RTM, developers can create their robot software with constructing of those software components.

Each RTC has ports as data-trasnporting endpoints, and a statemachine. To construct RT-system, connection between ports, and state activation is indispensable. To launch multiple RTCs also disturbs developers. `wasanbon` automates multiple RTC development in some aspects.

## Requirements

* [Python3.8](https://www.python.org/)
* [wasanbon1.2.0](https://github.com/wasanbon/wasanbon)
* [git bash](https://gitforwindows.org/) (Windows only)

## Features

* Repository and Package Management
* Semi-automated Build in Command Line
* Automatical Launch Configuration
* Automatic Launch, Configuration, Connection, and Activation of the RT-System

## Setup

> **Note**
>
> * Before installing wasanbon webframework, you should install [Python3.8](https://www.python.org/) and [wasanbon](https://github.com/wasanbon/wasanbon).
>
> * If you get a message stating that the path is not followed, such as the following, you need to set up the path.
>
>  ```bash
>   WARNING: The script wasanbon-webframework is installed in '/home/[user]/.local/bin' which is not on PATH.
>   Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
>  ```

```bash
git clone https://github.com/rsdlab/wasanbon_webframework.git
cd wasanbon_webframework

pip install --upgrade pip setuptools packaging importlib_metadata
pip install . --no-build-isolation
```
**Note:** Installation may fail due to dependency conflicts. Please check the dependency versions if you encounter any errors.

## Usage

* Start webframwork server

> **Note**
>
> * In a windows environment, files with `.sh` extension should be preconfigured to be executed by bash.
>
> * Stop the omniNames service before starting wasanbon-webframework, since the nameserver operation will be disabled.
>
> * The log file is output to the path where the command was executed.

```bash
wasanbon-webframework start
```

If you want to start other host's webframwork server,

```bash
wasanbon-webframework start --other_hosts
```

* Stop webframework server

```bash
wasanbon-webframework stop
```

or

```bash
wasanbon-webframework ps
wasanbon-webframework pskill
```

If you want to stop other host's server,

```bash
wasanbon-webframework stop --other_hosts
```

* Distributing user config file for Basic Authentication

```bash
wasanbon-webframework user_config_dist
```

## API Documents

After starting the server, please access `http://<your_ip>:8000/redoc` or `http://<your_ip>:8000/docs`.
