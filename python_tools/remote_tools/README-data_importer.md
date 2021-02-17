data_importer_client.py is a python reference client built on top of the REST APIs exposed by the backend service running on Thoughtspot cluster. It can be used to load the data into thoughtspot from remote machine too. "username" & "password" needs to be passed to ensure that only authenticated and authorized users are able to load the data.
The client can be used as is or can be used as a reference client to build a new tool on top of the REST APIs.

Usage :
Basic command to load the data :
python3 ./data_importer_client.py --cluster_host <ip-address of cluster node> --username <username> --target_database <target database> --target_table <target table> --source_files <space separated list of data files>
Note :
1. "localhost" is assumed if "--cluster_host" not specified.
2. "username" is the username that is used when logging into ThoughtSpot UI on browser.
3. Data to be loaded can be present in multiple space separated filepaths (typically in CSV format).

All the options of the tool can be seen with "--help" parameter :
python3 ./data_importer_client.py --help
usage: data_importer_client.py [-h] [--cluster_host CLUSTER_HOST]
                               [--service_port SERVICE_PORT] --username
                               USERNAME [--password PASSWORD]
                               --target_database TARGET_DATABASE
                               [--target_schema TARGET_SCHEMA] --target_table
                               TARGET_TABLE --source_files SOURCE_FILES
                               [SOURCE_FILES ...]
                               [--max_ignored_rows MAX_IGNORED_ROWS]
                               [--empty_target] [--validate_only]
                               [--file_target_dir FILE_TARGET_DIR]
                               [--type {CSV,DELIMITED,INTERNAL}]
                               [--field_separator FIELD_SEPARATOR]
                               [--trailing_field_separator]
                               [--enclosing_character ENCLOSING_CHARACTER]
                               [--escape_character ESCAPE_CHARACTER]
                               [--null_value NULL_VALUE] [--has_header_row]
                               [--flexible] [--date_converted_to_epoch]
                               [--date_time_format DATE_TIME_FORMAT]
                               [--date_format DATE_FORMAT]
                               [--time_format TIME_FORMAT]
                               [--second_fraction_start SECOND_FRACTION_START]
                               [--skip_second_fraction]
                               [--use_bit_boolean_values]
                               [--true_format TRUE_FORMAT]
                               [--false_format FALSE_FORMAT]

Load data into Thoughtspot cluster using data importer REST service.

optional arguments:
  -h, --help            show this help message and exit
  --cluster_host CLUSTER_HOST
                        URL of the ThoughtSpot cluster. Default is localhost.
  --service_port SERVICE_PORT
                        Port on which dataload service is listening.
  --username USERNAME   Username to log in. Same as ThoughtSpot username. User
                        must have ADMINISTRATION or DATAMANAGEMENT privilege
                        to be able to load data.
  --password PASSWORD   Password to log in. Same as ThoughtSpot password. User
                        must have ADMINISTRATION or DATAMANAGEMENT privilege
                        to be able to load data. This argument is optional
                        because of sensitivity. If password is not provided as
                        argument then user will be prompted to enter password
                        in stdin.
  --target_database TARGET_DATABASE
                        Name of target database.
  --target_schema TARGET_SCHEMA
                        Name of target schema.
  --target_table TARGET_TABLE
                        Name of target table.
  --source_files SOURCE_FILES [SOURCE_FILES ...]
                        Space separated list of files containing source data.
  --max_ignored_rows MAX_IGNORED_ROWS
                        If number of ignored rows exceeds this limit, load is
                        aborted.
  --empty_target        When set, current rows in target table or file are
                        dropped before loading new data.
  --validate_only       Used for validating the input. The loader will do
                        everything, short of commiting data to Falcon.
  --file_target_dir FILE_TARGET_DIR
                        If a valid path is given, instead of writing the data
                        to falcon manager, a DML file with the name
                        <cycle_id>.dml will be created under the given path.
  --type {CSV,DELIMITED,INTERNAL}
                        When non empty, represents type of source file. It can
                        be CSV or DELIMITED or INTERNAL.
  --field_separator FIELD_SEPARATOR
                        Applies to both CSV and DELIMITED, character that is
                        used to split record into fields e.g., comma.
  --trailing_field_separator
                        When set, all rows including the header (if
                        applicable) have a trailing field separator otherwise
                        the row would be considered as invalid row.
  --enclosing_character ENCLOSING_CHARACTER
                        String representing enclosing character in CSV source
                        format. This option is ignored for other source types.
  --escape_character ESCAPE_CHARACTER
                        String representing escape character in source data.
                        This applies only for DELIMITED data format. This
                        option is ignored for other data sources.
  --null_value NULL_VALUE
                        String that represents null values in input e.g.,
                        empty.
  --has_header_row      When set, input data file should have header row.
  --flexible            When set, attempts to load as follows. If extra
                        columns are present in input file, these are
                        discarded. If fewer columns are present in input file,
                        missing columns are filled with nulls. Otherwise, load
                        proceeds if input data file exactly matches target
                        schema.
  --date_converted_to_epoch
                        Whether date and time fields are already converted to
                        epoch in CSV source format. This option is ignored for
                        other source types.
  --date_time_format DATE_TIME_FORMAT
                        String that describes format of date time field
                        (specificied in strptime library) e.g., %Y%m%d
                        %H:%M:%S to represent 20011230 01:15:12.
  --date_format DATE_FORMAT
                        String that describes format of date field
                        (specificied in strptime library) e.g., %Y%m%d to
                        represent 20011230.
  --time_format TIME_FORMAT
                        String that describes format of time field
                        (specificied in strptime library) e.g., %H:%M:%S to
                        represent 01:15:12.
  --second_fraction_start SECOND_FRACTION_START
                        Must be a single character and identifies beginning
                        character of fractional component of seconds. Typical
                        value is ".", in other locales it can be ",". This
                        applies only when --skip_second_fraction is set.
  --skip_second_fraction
                        When set, skip fractional part of seconds e.g.,
                        milliseconds, microseconds or nanoseconds from
                        datetime or time values if present in source data.
                        This option is ignored for other source types. Note
                        that skipping fractional component (e.g. ms) from
                        input data can impact upsert behavior if input data
                        has non-unique fractional values for same time or
                        datetime values.
  --use_bit_boolean_values
                        When set, source CSV uses a bit for boolean values.
                        Here in source false is represented as 0x0 and true as
                        0x1. If false, boolean values are interpreted using
                        true_format and false_format. This option is ignored
                        for other source types.
  --true_format TRUE_FORMAT
                        String that represents True for boolean values in
                        input.
  --false_format FALSE_FORMAT
                        String that represents False for boolean values in
                        input.
