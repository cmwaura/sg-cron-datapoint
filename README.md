# sg-cron-datapoint

This repo contains a command-line tool that creates data points on one or more
Shotgun Sites. The data points are customizable and can be used to track data
related to other Shotgun entities (Shots, Assets, etc). Data points can be
tracked globally:

![](global_data_point.jpg?raw=true)

... on a per-Project basis (in this case, on Project "Sarabi"):

![](project_data_point.jpg?raw=true)

... or both. This stored data can then be used to build graphs or reports that
show trends over time, or can simply serve as a historical record. For example,
here is a quick graph created in Excel by using "Export All to Excel (csv)"
command:

![](graph.jpg?raw=true)

`sg-cron-datapoint` is meant to be run on a schedule, either via crontab, or
other process schedulers.

## Download

To download, clone this repo. Or, for those not familar with Git or GitHub,
click the green `Clone or download` button on this page:

https://github.com/shotgunsoftware/sg-cron-datapoint

... choose `Download ZIP`, and unzip the package into a directory of your
choice.

## Installation

These instructions assume familiarity with command-line applications—`Terminal`
on MacOS, `GitBash` or similar on Windows, and `Bash` on Linux. They also
assume that `python`, `pip`, and ideally `virtualenv` are already installed (if
you don't know if these items are installed on your system, ask your friendly
IT admin, or Google around with queries like "Install pip Windows").

Once you've verified that `python` and `pip` are installed, open a shell,
navigate into the folder that was created when you unzipped the
`sg-cron-datapoint` package, and check the `requirements.txt` file for a
list of required Python modules. These can be installed by running this command:

`pip install -r requirements.txt`

We recommend you do this from a `virtualenv` environment, in order to keep your
local system environment clean. Full `virtualenv` usage instructions can be
found here:

https://virtualenv.pypa.io/en/stable

## Authenticate

To gain access to a Shotgun Site, `sg-cron-datapoint` needs to reference
a Script Key. Visit the following url to learn how to create a Script
(Application) Key for your Shotgun Site:

https://support.shotgunsoftware.com/hc/en-us/articles/219031368-Create-and-manage-API-Scripts

Name the Script Key something like `sg-cron-datapoint`.

## Shotgun configuration

This script can create global or per Project data points, or both.

### Global data points

If you would like to track data globally, a `CustomNonProjectEntity` needs to be
nominated as the "Global Data Point" entity and enabled in Shotgun. This is the
entity that will be referenced as `global_data_point_entity` in the
`settings.yml` file. If you don't know how to use CustomEntities, visit the
following url (but remember to use a CustomNonProjectEntity, *not* a
CustomEntity):

https://support.shotgunsoftware.com/hc/en-us/articles/114094182834-Enabling-a-custom-entity

It's also a good idea to make a global Shotgun page to view Global Data Point
entity instances.

### Per project data points

This process is similar to creating global data points; if you would like to
track data per Project, a `CustomEntity` needs to be nomiated as the "Project
Data Point" entity and enabled in Shotgun. This is the entity that will be
referenced as `project_data_point_entity` in the `settings.yml` file. Remember
to use a `CustomEntity` for this and not a `CustomNonProjectEntity` (the
opposite of what you use for the Global Data Point).

## Settings

A `settings.yml` file must exist in the `sg-cron-datapoint` directory
with at least one Shotgun Site and its associated settings defined, like this:

```
https://example1.shotgunstudio.com:
  script_name: sg-cron-datapoint
  script_key: 123thisisafakescriptkeyexample456
  global_data_point_entity: CustomNonProjectEntity??
  track_globally:
    - entity_type: HumanUser
      filters: [["sg_status_list", "is", "act"]]
      write_to_field: sg_num_active_human_users
```

Note that multiple Sites can be defined:

```
https://example1.shotgunstudio.com:
  script_name: sg-cron-datapoint
  script_key: 123thisisafakescriptkeyexample456
  global_data_point_entity: CustomNonProjectEntity??
  track_globally:
    - entity_type: HumanUser
      filters: [["sg_status_list", "is", "act"]]
      write_to_field: sg_num_active_human_users
https://example2.shotgunstudio.com:
  script_name: sg-cron-datapoint.py
  script_key: 789thisisafakescriptkeyexample101
  global_data_point_entity: CustomNonProjectEntity??
  track_globally:
    - entity_type: HumanUser
      filters: [["sg_status_list", "is", "act"]]
      write_to_field: sg_num_active_human_users
```

Below is the full table of settings. Note that the `project_data_point_entity`
setting is not used in the examples above; see the "Testing" section for an
example.

| Setting name              | Type | Description                                                                                  |
| :-                        | :-   | :-                                                                                           |
| script_name               | str  | The name of the Shotgun Script key used to authenticate this script.                         |
| script_key                | str  | The "Application Key" value of the Shotgun Script key used to authenticate this script.      |
| global_data_point_entity  | str  | The `CustomNonProjectEntity` used as a "Global Data Point," e.g, `CustomNonProjectEntity02`. |
| project_data_point_entity | str  | The `CustomEntity` used as a "Project Data Point," e.g, `CustomEntity05`.                    |
| entity_type               | str  | The entity type whose data you want to track.                                               |
| filters                   | str  | A standard filters list to be used with an `sg.find` command. See the Shotgun Python API docs for details. |
| write_to_field            | str  | The name of the field on the Data Point entity that should track the requested data. No spaces allowed. If the field doesn't already exist in the Data Point entity schema, it will be created. |

## Usage

Type `./data_point.py -h` or `./data_point.py --help` from the
`sg-cron-datapoint` directory for usage details.

## Workflow

This script is meant to be run via crontab, or on a scheduler. That said, it's a
good idea to test it on the command-line first.

### Testing

After setting values in `settings.yml` and installing the Python modules
specified in the `requirements.txt` file, you're ready to create data points.
This can be done with a single command:

`./data_point.py --create`

Output should appear in your shell, similar to this:

```
Reading /Users/user/Documents/dev/repos/sg-cron-datapoint/settings.yml...
Connecting to https://example1.shotgunstudio.com...
Creating data point batch commands for all Projects...
Running batch create Shotgun command...
Created "2017_07_17_18-04-26" Global data point.
Created "2017_07_17_18-04-26" data point on Project "project_A."
Created "2017_07_17_18-04-26" data point on Project "project_B."
Created "2017_07_17_18-04-26" data point on Project "project_C."
```

You can then check your Shotgun Site's Global Data Points page (that you
created in the steps above) to see the new DataPoint instance. If you used the
example settings in this README.md file, a `sg_num_active_human_users` field
will be created in the Global Data Point schema and the total number of HumanUser
entities with their `sg_status_list` field set to `act` will be recorded there.
If you want to track other types of data, simply add them to the
`track_globally` or `track_per_project` lists. For example, if you want to also
track the number of Versions set to "In Progress," change your settings thusly:

```
https://example.shotgunstudio.com:
  script_name: sg-cron-datapoint
  script_key: 123thisisafakescriptkeyexample456
  global_data_point_entity: CustomNonProjectEntity??
  project_data_point_entity: CustomEntity??
  track_globally:
    - entity_type: HumanUser
      filters: [["sg_status_list", "is", "act"]]
      write_to_field: sg_num_active_human_users
  track_per_project:
    - entity_type: Version
      filters: [["sg_status_list", "is", "ip"]]
      write_to_field: sg_num_ip_versions
```

### Scheduling

Once you've tested the script and are happy with the result in Shotgun, you can
add it to a crontab. If you've set up a virtual environment, the crontab entry
will look something like this (this will run every night at midnight):

```
0 0 * * * source /path/to/repos/sg-cron-datapoint/venv/bin/activate; /path/to/repos/sg-cron-datapoint/data_point.py --create; deactivate
```

... and if you've installed the python requirements directly on your system,
it'll look something like this:

```
0 0 * * * /path/to/repos/sg-cron-datapoint/data_point.py --create
```

If you'd like to run the script on a different schedule, just Google around for
crontab examples.
