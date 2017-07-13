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

    def __init__(self, create_data_points):
        """
        Defines variables to share across methods, sets up logging, Shotgun
        connections, reads settings, and runs the _create_data_points method,
        if asked for.

        :param bool create_data_points: Whether or not a data point is created.
        """

        # Don't do anything unless the user has asked to create a data point.
        if create_data_points:

            # Initialize shared variables.
            self._sites = {}
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
            logging.error(
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
        Adds sg handles to the sites dict and removes credentials.
        """

        # Grab a Python API handle for each Shotgun Site and add it to the
        # self._sites dict.
        for site_url, credentials in self._sites.iteritems():

            if not credentials.get("script_name") or not credentials.get("script_key"):
                logging.error(
                    "Bad or missing settings for %s in settings.yml, exiting." % site_url
                )
                return

            logging.info("Connecting to %s..." % site_url)
            credentials["sg"] = shotgun_api3.Shotgun(
                site_url,
                script_name=credentials["script_name"],
                api_key=credentials["script_key"],
            )

            # We don't need these anymore, so lets clear them out of memory.
            credentials.pop("script_name", None)
            credentials.pop("script_key", None)

    def _create_data_points(self):
        """
        Creates one data point for each Shotgun Site in the self._sites dict.
        """

        # Loop through each Site and create a data point.
        for site_url, site_info in self._sites.iteritems():

            sg = site_info["sg"]
            data_point_entity = site_info["data_point_entity"]
            data_point_schema = sg.schema_field_read(data_point_entity)
            data = {"code": self._datestamp}

            # Loop through to_track list and add any data points we find.
            for track in site_info["to_track"]:

                # Add the write_to_field to the data_point_entity schema if it
                # doesn't exist.
                if not track["write_to_field"] in data_point_schema.keys():
                    field = sg.schema_field_create(
                        data_point_entity,
                        "number",
                        track["write_to_field"].replace("sg_", ""),
                    )
                    if field != track["write_to_field"]:
                        raise ValueError(
                            "Attempted to create field %s on %s schema, but got %s." % (
                                track["write_to_field"],
                                data_point_entity,
                                field,
                            )
                        )
                    else:
                        logging.info(
                            "Created field %s on %s." % (
                                track["write_to_field"],
                                data_point_entity,
                            )
                        )

                # Find all entity instances that match the field/value criteria.
                entities = sg.find(
                    track["entity_type"],
                    [
                        [track["field_to_track"], "is", track["value_to_track"]]
                    ]
                )

                data[track["write_to_field"]] = len(entities)

            # Create our data point and tell the logger about it.
            data_point = sg.create(data_point_entity, data)
            logging.info("Created data point: %s" % data_point)


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

    # Pass our command-line arguments to the DataPoint class.
    else:
        args = vars(parser.parse_args())
        DataPoint(
            args["create_data_points"],
        )
