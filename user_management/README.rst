SYNC USERS AND GROUPS
This folder contains wrapper code for using the ThoughtSpot APIs related to users and groups from Python. Additionally it contains several helpful tools that make use of the API and can make your life easier when dealing with users and groups.

So why use this API wrapper instead of calling the APIs directly? Mainly because, if you are using Python to call the APIs, this file has been tested and known to work. It includes validation code to (try to) prevent you from making hard to debug errors when using the sync and other web calls. If you are not using Python, it provides good example code for creating your own interface to the APIs.

tsUserGroupApi.py
This file is a Python module that provides abstraction for the APIs. Classes from this module abstract away the complexity of the API and make it easier to use. This file has been used to create API interfaces in hours instead of days. Note that the tsUserGroupApi.py file will work with the latest version of ThoughtSpot and have the latest relevant API support. Older versions will be tagged with the name of the version, e.g. tsUserGroupApi_4_2.py should work with version 4.2, but not 4.4 and later.

Always refer the code for actual details. And you can view the test classes (discussed below) to see how to use the classes for different operations.

Current list of classes in the module:

class Visibility - contains options for visibility of users and groups
class User - represents a user in ThoughtSpot
class Group - represents a group in ThoughtSpot
class UsersAndGroups - represents a collection of users and groups
class UGJsonReader - reads users and groups from valid JSON
class SyncUserAndGroups - Supports the calls to ThoughtSpot to sync, etc.
class UGXLSWriter - will write users and groups to Excel
Please note that this code was built and tested with Python 2.7, which is the version that runs on ThoughtSpot.

test_xxx.py
These are the various test cases used to verify the code works. These files are very convenient to see how to use the classes in the API.

Stand Alone Scripts
To assist with system management and perform some actions that are not available from the UI, several scripts have been created. These should work as-is, as long as the correct parameters are passed.

WARNING: You usually have to use HTTPS for the URLs or you will get HTTP 405 errors.

How to deploy the code
To run these scripts, you will need to put tsUserGroupApi.py and the scripts into the same directory of your choice and run from there.

You will also need to have Python 2.7 running in your environment. Python 3 might work, but it's not been tested.

get_users.py
This script will retrieve a list of users and groups from ThoughtSpot and write to either JSON or Excel.

Usage: get_users [flags]

To get a full list of the available flags, run python get_users.py --help

sync_from_excel.py
This script will sync users and groups from a formatted Excel file to ThoughtSpot. The format is the same as that returned by get_users.py. So a common workflow would be to run get_users.py, edit the file, then run sync_from_excel.py.

Usage: sync_from_excel [flags]

To get a full list of the available flags, run python sync_from_excel.py --help

delete_ugs.py
This file will delete a list of users and/or groups from ThoughtSpot by userid.

Usage: delete_ugs [flags]

To get a full list of the available flags, run python delete_ugs.py --help

transfer_ownership.py
This script will transfer ownership of all content from one user to another.

Usage: python transfer_ownership.ui [flags]

To get a full list of the available flags, run python transfer_ownership.py --help

validate_json.py
This simple script will verify that JSON is valid. Even if you are not using the Python APIs, it's a simple way to validate your JSON to avoid errors calling the API. Invalid JSON will give an error, but it's often hard understand.

Usage: validate_json.py where is the name of a file containing JSON.