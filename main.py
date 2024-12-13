#
# Name: Move By Category
# Description: A script to move a completed download based on category
#
# Copyright (C) Dosk3n
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import sys
import shutil
from datetime import datetime

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS = 93
POSTPROCESS_ERROR = 94
POSTPROCESS_NONE = 95

# Check if the script is called from NZBGet
if 'NZBOP_SCRIPTDIR' not in os.environ:
    print("This script can only be called from NZBGet.")
    sys.exit(POSTPROCESS_ERROR)

print("[DETAIL] Script successfully started")
sys.stdout.flush()

# Options passed to script as environment variables
# Check required options
required_options = (
    "NZBPO_NAMEOFCATEGORY",
    "NZBPO_NEWLOCATIONOFCATEGORY"
)
for optname in required_options:
    if optname not in os.environ:
        print(f"[ERROR] Option {optname[6:]} is missing in configuration file. Please check script settings")
        sys.exit(POSTPROCESS_ERROR)

# Check if the script is executed from settings page with a custom command
command = os.environ.get("NZBCP_COMMAND")
test_mode = command == "Test"
if command is not None and not test_mode:
    print("[ERROR] Invalid command " + command)
    sys.exit(POSTPROCESS_ERROR)

NameOfCategory = os.environ["NZBPO_NAMEOFCATEGORY"]
NewLocationOfCategory = os.environ["NZBPO_NEWLOCATIONOFCATEGORY"]

if test_mode:
    print(f"[DETAIL] Script successfully invoked with params: \nNameOfCategory: {NameOfCategory} \nNewLocationOfCategory: {NewLocationOfCategory}")
else:
    # Only proceed if the category matches
    category = os.environ.get('NZBPP_CATEGORY')
    if category != NameOfCategory:
        print(f"[INFO] Skipping move, category is not {NameOfCategory}.")
        sys.exit(NZBGET_POSTPROCESS_NONE)

    # Check the overall download status
    total_status = os.environ.get('NZBPP_TOTALSTATUS')
    par_status = os.environ.get('NZBPP_PARSTATUS')
    unpack_status = os.environ.get('NZBPP_UNPACKSTATUS')

    # Initialize status flag
    status_ok = True

    # Verify download success
    if total_status != 'SUCCESS':
        print("[ERROR] Download failed with status %s." % total_status)
        status_ok = False

    # Verify par-check/repair status
    if par_status in ['1', '4']:
        print("[ERROR] Par-repair failed.")
        status_ok = False

    # Verify unpack status
    if unpack_status == '1':
        print("[ERROR] Unpack failed.")
        status_ok = False

    # Exit if there were any errors
    if not status_ok:
        sys.exit(NZBGET_POSTPROCESS_ERROR)

    # Everything looks ok so proceed

    # Get the original download directory
    download_directory = os.environ['NZBPP_DIRECTORY']

    # Resolve any symlinks
    destination_real = os.path.realpath(NewLocationOfCategory)
    directory_real = os.path.realpath(download_directory)

    # Check if source and destination directories exist
    if not os.path.isdir(directory_real):
        print("[ERROR] Current destination directory \"%s\" does not exist." % download_directory)
        sys.exit(NZBGET_POSTPROCESS_ERROR)

    if not os.path.isdir(destination_real):
        print("[ERROR] New destination directory \"%s\" does not exist." % NewLocationOfCategory)
        sys.exit(NZBGET_POSTPROCESS_ERROR)

    # Skip moving if already in the destination directory
    if destination_real == os.path.dirname(directory_real):
        print("[INFO] Skipping move, download directory \"%s\" is already in the proper destination." % download_directory)
        sys.exit(NZBGET_POSTPROCESS_NONE)

    # Move the download directory
    print("[INFO] Moving download directory")
    print("[INFO] - Source: %s" % directory_real)
    print("[INFO] - Destination: %s" % destination_real)

    try:
        shutil.move(directory_real, destination_real)
    except Exception as e:
        print("[ERROR] Failed to move download directory: %s" % str(e))
        sys.exit(NZBGET_POSTPROCESS_ERROR)

    # Update NZBGet with the new directory path
    new_directory = os.path.join(NewLocationOfCategory, os.path.basename(download_directory))
    print("[NZB] DIRECTORY=%s" % new_directory)

# All OK, returning exit status 'POSTPROCESS_SUCCESS' (int <93>) to let NZBGet know
# that our script has successfully completed.
sys.exit(POSTPROCESS_SUCCESS)
