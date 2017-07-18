#!/usr/bin/env python

# Copyright 2017 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license agreement
# provided at the time of installation or download, or which otherwise accompanies
# this software in either electronic or hard copy form.
#

"""
To learn more about this script, see the README.md file in this directory, or
run `./data_point.py -h` or `./data_point.py --help` for usage information.
"""

import os
import sys
import yaml
import logging
import datetime
import argparse
import shotgun_api3

_DESCRIPTION = "This script creates a data point in one or more Shotgun Sites \
that stores field/value data specified in a settings.yml file. See README.md \
for more details."


class DataPoint(object):
    """
    This class contains methods related to reading settings, querying Shotgun,
    and creating data point records.
    """

    def __init__(self):
        """
        Defines variables to share across methods, sets up logging, Shotgun
        connections, reads settings, and runs the _create_data_points method,
        if asked for.

        :param bool create_data_points: Whether or not a data point is created.
        """

        # Initialize shared variables.
        self._sites = {}
        self._batch_data = []
        self._cur_dir = os.path.dirname(os.path.abspath(__file__))

        # Create a datestamp var for stamping logs and naming data points.
        self._datestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")

        # Set up everything we need to log output.
        self._set_up_logging()

        # Read settings, connect to sg, and create one or more data points.
        self._read_settings()
        self._connect_to_sg()
        self._create_data_points()

    def _set_up_logging(self):
        """
        Creates logs directory and sets up logger-related stuffs.
        """

        logs_dir = os.path.join(self._cur_dir, "logs")

        # Create a logs directory if it doesn't exist.
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Create a log file path.
        log = os.path.join(logs_dir, "%s.log" % self._datestamp)

        # Set the logging level.
        logging_level = logging.INFO

        # Set up our logging.
        logging.basicConfig(
            filename=log,
            level=logging_level,
            format="%(levelname)s: %(asctime)s: %(message)s",
        )
        logging.getLogger().addHandler(logging.StreamHandler())

    def _read_settings(self):
        """
        Reads in and validates a settings.yml file.
        """

        settings_file = os.path.join(self._cur_dir, "settings.yml")

        # Tell the logger which file we're trying to read.
        logging.info("Reading %s..." % settings_file)

        # Grab our user settings and barf if something is wrong.
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as fh:
                    sites = yaml.load(fh)
            except Exception, e:
                raise ValueError("Could not parse %s: %s" % (settings_file, str(e)))
        else:
            raise ValueError(
                "Did not find %s. See README.md for details." % settings_file
            )
            return
        if not sites:
            raise ValueError(
                "Settings dict is empty (bad %s file?), exiting." % settings_file
            )

        # Return the Sites dict if everything is copasetic.
        self._sites = sites

    def _connect_to_sg(self):
        """
        Adds sg handles to the self._sites dict and removes credentials.
        """

        # Grab a Python API handle for each Shotgun Site and add it to the
        # self._sites dict.
        for site_url, credentials in self._sites.iteritems():

            if not credentials.get("script_name") or not credentials.get("script_key"):
                raise ValueError(
                    "Bad or missing settings for %s in settings.yml, exiting." % site_url
                )

            logging.info("Connecting to %s..." % site_url)
            credentials["sg"] = shotgun_api3.Shotgun(
                site_url,
                script_name=credentials["script_name"],
                api_key=credentials["script_key"],
            )

            # We don't need these anymore, so lets clear them out of memory.
            credentials.pop("script_name", None)
            credentials.pop("script_key", None)

    def _prep_schema(self, entity, site_info, to_track):
        """
        Creates required fields on a data point entity if they don't already
        exist.

        :param str entity: A SG CustomEntity or CustomNonProjectEntity.
        :param dict site_info: A settings dict related to one SG Site.
        :param list to_track: A list of dicts containing info about what field
                              data to track and where to write it to.
        :raises: ValueError if a schema field can't be created.
        """

        # Grab the entity's schema.
        data_point_schema = site_info["sg"].schema_field_read(entity)

        # Loop through the to_track list and add any fields we find.
        for track in to_track:

            # Add the write_to_field to the entity schema if it doesn't exist.
            if not track["write_to_field"] in data_point_schema.keys():
                field = site_info["sg"].schema_field_create(
                    entity,
                    "number",
                    track["write_to_field"].replace("sg_", ""),
                )
                if field != track["write_to_field"]:
                    raise ValueError(
                        "Attempted to create field %s on %s schema, but got %s." % (
                            track["write_to_field"],
                            entity,
                            field,
                        )
                    )
                else:
                    logging.info(
                        "Created field %s on %s." % (
                            track["write_to_field"],
                            entity,
                        )
                    )

    def _add_point(self, entity, site_info, to_track, project=None):
        """
        Creates a data point entry in self._batch_data for each item in the
        to_track list.

        :param str entity: A SG CustomEntity or CustomNonProjectEntity.
        :param dict site_info: A settings dict related to one SG Site.
        :param list to_track: A list of dicts containing info about what field
                              data to track and where to write it to.
        :param dict project: A standard SG Project dict.
        """

        # Start our batch create data dict.
        data = {"code": self._datestamp}
        if project:
            data["project"] = project

        # Loop through the track list and add any data points we find.
        for track in to_track:

            # Copy the filters list so we don't end up bloating it as we loop
            # through to_track.
            filters = list(track["filters"])

            # If we've got a Project, add it to the filters list.
            if project:
                filters.append(["project", "is", project])

            # Add exceptions to filters list for weird cases (like built-in
            # HumanUsers).
            if track["entity_type"] == "HumanUser":
                filters.append(
                    ["name", "not_in", ["Shotgun Support", "Template User"]]
                )

            # Find all entity instances that match the field/value criteria.
            entities = site_info["sg"].find(track["entity_type"], filters)

            # Count our instances and assign the number to write_to_field.
            data[track["write_to_field"]] = len(entities)

        # Add our data point to the batch command list.
        self._batch_data.append(
            {
                "request_type": "create",
                "entity_type": entity,
                "data": data,
            }
        )

    def _create_data_points(self):
        """
        Loops through the sites dict, and runs _prep_schema and _add_point
        depending on whether global and/or Project data entities are defined.
        """

        # Loop through each Site and create a data point.
        for site_url, site_info in self._sites.iteritems():

            if not site_info.get("global_data_point_entity") and \
                not site_info.get("project_data_point_entity"):
                    logging.error(
                        "No data point entities defined for %s, skipping Site." % site_url
                    )
                    continue

            # If we've got a global_data_point_entity, prep its schema and add
            # a data point to self._batch_data.
            if site_info.get("global_data_point_entity"):
                global_data_point_entity = site_info["global_data_point_entity"]
                self._prep_schema(
                    global_data_point_entity,
                    site_info,
                    site_info["track_globally"],
                )
                self._add_point(
                    global_data_point_entity,
                    site_info,
                    site_info["track_globally"],
                )

            # project_data_point_entity is different than the
            # global_data_point_entity because we need to create a data point
            # for each Project. Start off the same by prepping the schema.
            if site_info.get("project_data_point_entity"):
                project_data_point_entity = site_info["project_data_point_entity"]
                self._prep_schema(
                    project_data_point_entity,
                    site_info,
                    site_info["track_per_project"],
                )

                # Ignore these special Projects.
                template_and_demo_projects = [
                    "Template Project",
                    "Motion Capture Template",
                    "Motion Capture Template",
                    "Demo: Animation",
                    "Demo: Game",
                    "Game Template",
                    "Film Template",
                    "TV Series Template",
                    "Demo: Animation with Cuts",
                ]

                # Find all relevant Projects.
                projects = site_info["sg"].find(
                    "Project",
                    [
                        ["name", "not_in", template_and_demo_projects],
                    ],
                    ["name"],
                )

                # Tell the logger what we're doing b/c this can be slow.
                logging.info(
                    "Creating data point batch commands for all Projects..."
                )

                # Add all the Project data points to self._batch_data.
                for project in projects:
                    self._add_point(
                        project_data_point_entity,
                        site_info,
                        site_info["track_per_project"],
                        project,
                    )

            # If we've got something in self._batch_data, send it off to SG.
            if self._batch_data:
                logging.info("Running batch create API command...")
                site_info["sg"].batch(self._batch_data)
                for data_point in self._batch_data:
                    if data_point["entity_type"] == site_info.get("project_data_point_entity"):
                        logging.info(
                            "Created \"%s\" data point on Project \"%s.\"" % (
                                data_point["data"]["code"],
                                data_point["data"]["project"]["name"],
                            )
                        )
                    else:
                        logging.info(
                            "Created \"%s\" Global data point." % (
                                data_point["data"]["code"],
                            )
                        )
            else:
                logging.Error("Nothing to do!")

if __name__ == "__main__":
    """
    Handles command-line interface and passes args to the DataPoint class.
    """

    # Initialize a command-line argument parser.
    parser = argparse.ArgumentParser(
        description=_DESCRIPTION
    )

    # Add arguments to the parser.
    parser.add_argument(
        "-c",
        "--create_data_points",
        help="Create a data point in Shotgun.",
        action="store_true",
        required=False,
    )

    # Print script usage if no arguments are passed.
    if len(sys.argv) < 2:
        print "Usage: report.py --help"

    # Run the DataPoint class if create_data_points has been specified.
    else:
        args = vars(parser.parse_args())
        if args["create_data_points"]:
            DataPoint()
