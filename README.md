# pi-datapoint-localinstall

This repo contains a command-line tool that creates a data point on one or more
Shotgun Sites. The data point is customizable and can be used to track and count
field data from other Shotgun entities:

![](data_point.jpg?raw=true)

This stored data can then be used to build graphs or reports that show trends
over time, or simply be a historical record.

`pi-datapoint-localinstall` is meant to be run on a schedule, either via
crontab, or other process schedulers.

## Download

To download, simply clone this repo. Or, for those not familar with Git or
GitHub, click the green `Clone or download` button on this page:

https://github.com/shotgunsoftware/pi-datapoint-localinstall

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
`pi-report-localinstall` package, and check the `requirements.txt` file for a
list of required Python modules. These can be installed by running this command:

`pip install -r requirements.txt`

We recommend you do this from a `virtualenv` environment, in order to keep your
local system environment clean. Full `virtualenv` usage instructions can be
found here:

https://virtualenv.pypa.io/en/stable

## Authenticate

To gain access to a Shotgun Site, `pi-datapoint-localinstall` needs to reference
a Script Key. Visit the following url to learn how to create a Script
(Application) Key for your Shotgun Site:

https://support.shotgunsoftware.com/hc/en-us/articles/219031368-Create-and-manage-API-Scripts

Name the Script Key something like `pi-datapoint-localinstall.py`.

## Shotgun configuration

A `CustomNonProjectEntity` needs to be nominated as the "Data Point" entity and
enabled in Shotgun. This is the entity that will be referenced in the
`settings.yml` file. If you don't know how to do that, visit this url to learn
how to add CustomEntities (but remember to use a CustomNonProjectEntity, *not* a
CustomEntity):

https://support.shotgunsoftware.com/hc/en-us/articles/114094182834-Enabling-a-custom-entity

It's also a good idea to make a global Shotgun page to view the Data Point
entity instances.

## Settings

A `settings.yml` file must exist in the `pi-datapoint-localinstall` directory
with at least one Shotgun Site and its associated settings defined, like this:

```
https://example.shotgunstudio.com:
  script_name: pi-datapoint-localinstall.py
  script_key: 123thisisafakescriptkeyexample456
  data_point_entity: CustomNonProjectEntity??
  to_track:
    - entity_type: HumanUser
      field_to_track: sg_status_list
      value_to_track: act
      write_to_field: sg_num_active_human_users
```

| Setting name      | Type | Description                                                                                    |
| :-                | :-   | :-                                                                                             |
| script_name       | str  | The name of the Shotgun Script key used to authenticate this script.                           |
| script_key        | str  | The "Application Key" value of the Shotgun Script key used to authenticate this script.        |
| data_point_entity | str  | The `CustomNonProjectEntity` used as a "Data Point," e.g, `CustomNonProjectEntity05`.          |
| entity_type       | str  | The entity type whose field you want to track.                                                 |
| field_to_track    | str  | The field on `entity_type` that you would like to track.                                       |
| value_to_track    | str  | The value of `field_to_track` to track.                                                        |
| write_to_field    | str  | The name of the field on `data_point_entity` to store the `value_to_track`. No spaces allowed. If the field doesn't already exist in the `data_point_entity` schema, it will be created. |

Note that multiple Sites can be defined:

```
https://example1.shotgunstudio.com:
  script_name: pi-datapoint-localinstall.py
  script_key: 123thisisafakescriptkeyexample456
  data_point_entity: CustomNonProjectEntity??
  to_track:
    - entity_type: HumanUser
      field_to_track: sg_status_list
      value_to_track: act
      write_to_field: sg_num_active_human_users
https://example2.shotgunstudio.com:
  script_name: pi-datapoint-localinstall.py
  script_key: 789thisisafakescriptkeyexample101
  data_point_entity: CustomNonProjectEntity??
  to_track:
    - entity_type: HumanUser
      field_to_track: sg_status_list
      value_to_track: act
      write_to_field: sg_num_active_human_users
```

## Usage

Type `./data_point.py -h` or `./data_point.py --help` from the
`pi-datapoint-localinstall` directory for usage details.

## Workflow

This script is meant to be run via crontab, or on a scheduler. That said, it's a
good idea to test it on the command-line first.

### Testing

After setting values in `settings.yml` and installing the python modules
specified in the `requirements.txt` file, you're ready to create a data point.
This can be done with a single command:

`./data_point.py --create`

Output should appear in your shell, similar to this:

```
Reading /path/to/repos/pi-report-localinstall/settings.yml...
Connecting to https://example.shotgunstudio.com...
Created data point: {'code': '2017_07_13_11-09-12', 'type': 'CustomNonProjectEntity02', 'id': 36, 'sg_num_active_human_users': 5, 'sg_num_ip_versions': 73}
```

You can then check your Shotgun Site's global Data Points page (that you
created) to see the new DataPoint instance. If you used the example settings in
this README.md file, a `sg_num_active_human_users` field will be created in the
DataPoint schema and the total number of HumanUser entities with their
`sg_status_list` field set to `act` will be recorded there. If you want to track
other types of data, simply add them to the `to_track` list. For example, if you
want to track the number of Versions set to Active, change your settings thusly:

```
https://example.shotgunstudio.com:
  script_name: pi-datapoint-localinstall.py
  script_key: 123thisisafakescriptkeyexample456
  data_point_entity: CustomNonProjectEntity??
  to_track:
    - entity_type: HumanUser
      field_to_track: sg_status_list
      value_to_track: act
      write_to_field: sg_num_active_human_users
    - entity_type: Version
      field_to_track: sg_status_list
      value_to_track: act
      write_to_field: sg_num_act_versions
```

### Scheduling

Once you've tested the script and are happy with the result in Shotgun, you can
add it to a crontab. If you've set up a virtual environment, the crontab entry
will look something like this (this will run every night at midnight):

```
0 0 * * * source /path/to/repos/pi-report-localinstall/venv/bin/activate; /path/to/repos/pi-report-localinstall/data_point.py -c; deactivate
```

... and if you've installed the python requirements directly on your system,
it'll look something like this:

```
0 0 * * * /path/to/repos/pi-report-localinstall/data_point.py -c
```

If you'd like to run the script on a different schedule, just Google around for
crontab examples.
