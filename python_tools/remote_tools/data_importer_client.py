#!/usr/bin/env python3
# Copyright: ThoughtSpot Inc 2020
"""
This client can be used to establish a network connection with the
ETL HTTP Server over an HTTPS channel. The ETL HTTP Server is a
wrapper over the TSLoad interface. This client is used to remotely
load data from one or more source files into a ThoughtSpot instance
using ThoughtSpot credentials.
"""

import argparse
from getpass import getpass
import json
import pprint
import sys
import time
import urllib
import urllib3

import requests
from requests_toolbelt import MultipartEncoder

# Disable warning that comes due to using verify=False in all the calls
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# region CORE_METHODS
# Following methods are the ones that are needed when writing a custom ETL
# scripts. The rest of the file have methods needed to write a simple ETL
# CLI client for testing.

def getBaseUrl(hostport):
    """
    Get the base url for interacting with the ETL HTTP Server.
    Args:
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
    """
    return 'https://' + hostport + '/ts_dataservice/v1/public'

def getLoadsUrl(hostport, cycle_id):
    """
    Get the base url pointing to a specific load cycle.
    Args:
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of the load cycle.
    """
    return getBaseUrl(hostport) + '/loads/' + cycle_id

def getCycleDetails(hostport, start_load_response):
    """
    Get load cycle details from the server's response to start load request.
    Args:
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        start_load_response (Response): Server's response to start load request.
    """
    try:
        ret = start_load_response.json()
        cycle_id = ret['cycle_id']
        load_hostport = hostport
        if 'node_address' in ret:
            load_hostport = (ret['node_address']['host']
                             + ':' + str(ret['node_address']['port']))
        print('Load created with cycle_id:', cycle_id)
        print('Scheduled at url:', load_hostport)
        return load_hostport, cycle_id
    except:
        raise Exception('Cannot parse startLoad response: '
                        + start_load_response.text)

def ping(hostport):
    """
    Send ping request to ETL HTTP Server.
    Args:
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
    """
    response = requests.get(getBaseUrl(hostport) + '/ping', verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('ping request failed. Response: ' + response.text)
    return response

def login(session, hostport, username, password):
    """
    Send login request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        args (dict): Parsed command line arguments.
    """
    json_data = urllib.parse.urlencode({'username':username,
                                        'password':password})
    headers = {'Content-type':'application/x-www-form-urlencoded',
               'Accept':'text/plain'}
    print(f"Calling {getBaseUrl(hostport)}/session with {json_data}")
    response = session.post(getBaseUrl(hostport) + '/session', data=json_data,
                            headers=headers, verify=False)
    if not response.ok: # 2xx response code
        raise Exception('login request failed. Response: ' + response.text)
    print(f"Successful login: {response.text}")
    return response

def startLoad(session, hostport, load_params):
    """
    Send start load request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        args (dict): Parsed command line arguments.
    """
    json_data = json.dumps(load_params)
    response = session.post(getBaseUrl(hostport) + '/loads', data=json_data,
                            verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Start request failed. Response: ' + response.text)
    return getCycleDetails(hostport, response)

def load(session, hostport, cycle_id, file_path):
    """
    Send data load request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
        file_path (str): Path of source data file.
    """
    with open(file_path, 'rb') as f:
        form = MultipartEncoder({
            "documents": ('filename', f, "application/octet-stream"),
        })
        headers = {"Content-Type": form.content_type}
        response = session.post(getLoadsUrl(
            hostport, cycle_id), headers=headers, data=form, verify=False)
        if response.status_code // 100 != 2:  # 2xx response code
            raise Exception('Load request failed. Response: ' + response.text)
    print('Data from', file_path, 'sent to server successfully.')

def commitLoad(session, hostport, cycle_id):
    """
    Send commit load request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
    """
    response = session.post(getLoadsUrl(hostport, cycle_id) + '/commit',
                            verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Commit request failed. Response: ' + response.text)
    return response

def getLoadParams(session, hostport, cycle_id):
    """
    Send get load parameters request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
    """
    response = session.get(getLoadsUrl(hostport, cycle_id) + '/input_summary',
                           verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Load params request failed. Response: '
                        + response.text)
    return response

def getStatus(session, hostport, cycle_id):
    """
    Send get load status request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
    """
    response = session.get(getLoadsUrl(hostport, cycle_id), verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Status request failed. Response: ' + response.text)
    return response

def getBadRecords(session, hostport, cycle_id):
    """
    Send get bad records request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
    """
    response = session.get((getLoadsUrl(hostport, cycle_id)
                            + '/bad_records_file'), verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Bad records request failed. Response: '
                        + response.text)
    return response

def cancelLoad(session, hostport, cycle_id):
    """
    Send cancel load request to ETL HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        hostport (str): Host and port of the ETL HTTP Server separated by colon.
        cycle_id (str): Unique identifier of load cycle.
    """
    response = session.post(getLoadsUrl(hostport, cycle_id) + '/cancel',
                            verify=False)
    if response.status_code // 100 != 2: # 2xx response code
        raise Exception('Cancel request failed. Response: ' + response.text)
    return response

# endregion CORE_METHODS

def add_param(param_dict, key, value, default=None):
    """
    Add a parameter to the dictionary if its value is non-default.
    Args:
        param_dict (dict): Dictionary containing parameters.
        key (str): Key of parameter to be added.
        value (obj): Value to be added.
        default (obj): Default value of parameter.
    """
    if value is not None and value != default:
        param_dict[key] = value

def makeLoadParams(args):
    """
    Create load parameters for start load request out of command line arguments.
    Args:
        args (dict): Parsed command line arguments.
    """
    load_params = {'target': {},
                   'format': {'date_time': {},
                              'boolean': {}},
                   'load_options': {},
                   'advanced_options': {}}
    add_param(load_params['target'], 'database', args.target_database)
    add_param(load_params['target'], 'schema', args.target_schema)
    add_param(load_params['target'], 'table', args.target_table)

    if len(load_params['target']) == 0:
        del load_params['target']

    add_param(load_params['format'], 'type', args.type)
    add_param(load_params['format'], 'field_separator', args.field_separator)
    add_param(load_params['format'], 'trailing_field_separator',
              args.trailing_field_separator, False)
    add_param(load_params['format'], 'enclosing_character',
              args.enclosing_character)
    add_param(load_params['format'], 'escape_character', args.escape_character)
    add_param(load_params['format'], 'null_value', args.null_value)
    add_param(load_params['format'], 'has_header_row',
              args.has_header_row, False)
    add_param(load_params['format'], 'flexible', args.flexible, False)
    add_param(load_params['format']['date_time'], 'converted_to_epoch',
              args.date_converted_to_epoch, False)
    add_param(load_params['format']['date_time'], 'date_format',
              args.date_format)
    add_param(load_params['format']['date_time'], 'time_format',
              args.time_format)
    add_param(load_params['format']['date_time'], 'date_time_format',
              args.date_time_format)
    add_param(load_params['format']['date_time'], 'second_fraction_start',
              args.second_fraction_start)
    add_param(load_params['format']['date_time'], 'skip_second_fraction',
              args.skip_second_fraction, False)

    if len(load_params['format']['date_time']) == 0:
        del load_params['format']['date_time']

    add_param(load_params['format']['boolean'], 'use_bit_values',
              args.use_bit_boolean_values, False)
    add_param(load_params['format']['boolean'], 'true_format', args.true_format)
    add_param(load_params['format']['boolean'], 'false_format',
              args.false_format)

    if len(load_params['format']['boolean']) == 0:
        del load_params['format']['boolean']

    if len(load_params['format']) == 0:
        del load_params['format']

    add_param(load_params['load_options'], 'empty_target',
              args.empty_target, False)
    add_param(load_params['load_options'], 'max_ignored_rows',
              args.max_ignored_rows)

    if len(load_params['load_options']) == 0:
        del load_params['load_options']

    add_param(load_params['advanced_options'], 'validate_only',
              args.validate_only, False)
    add_param(load_params['advanced_options'], 'file_target_dir',
              args.file_target_dir)

    if len(load_params['advanced_options']) == 0:
        del load_params['advanced_options']

    print('Created load params: ', load_params)
    return load_params

def formatTime(epoch_microseconds):
    """
    Get human readable time from microseconds epoch.
    Args:
        epoch_microseconds (str): Number of microseconds passed since epoch.
                                  This argument can be string or int.
    """
    local_time = time.localtime(int(epoch_microseconds) // 1000000)
    return time.strftime('%a, %d %b %Y %H:%M:%S %Z', local_time)

def formatSize(size_bytes):
    """
    Get human readable size from number of bytes.
    Args:
        size_bytes (str): Size in number of bytes. Can be string or int.
    """
    readable_size = int(size_bytes)
    if readable_size < 1024:
        return '%d Bytes' % (readable_size)
    for prefix in ['', 'Ki', 'Mi', 'Gi']:
        if readable_size < 1024:
            return '%.2f %sB' % (readable_size, prefix)
        readable_size = readable_size / 1024
    return '%.2f TiB' % readable_size

def formatCount(num):
    """
    Get human readable number from large number.
    Args:
        num (str): Large number. Can be string or int.
    """
    count = int(num)
    if count < 1000:
        return '%d' % (count)
    for suffix in ['', 'K', 'M']:
        if count < 1000:
            return '%.1f%s' % (count, suffix)
        count = count / 1000
    return '%.1fT' % (count)

def AlterStatus(status):  # pylint: disable=too-many-branches
    """
    Change status to have human readable fields.
    Args:
        status (dict): Status response received from server.
    """
    if 'start_time' in status:
        status['start_time'] = formatTime(status['start_time'])
    if 'create_timestamp' in status:
        if 'start_time' not in status:
            status['start_time'] = formatTime(status['create_timestamp'])
        del status['create_timestamp']
    if 'end_time' in status:
        status['end_time'] = formatTime(status['end_time'])
    if 'last_update_timestamp' in status:
        if 'end_time' not in status:
            status['end_time'] = formatTime(status['last_update_timestamp'])
        del status['last_update_timestamp']
    if 'ingested_network_bw' in status:
        status['ingested_network_bw'] = (
            formatSize(status['ingested_network_bw'])
        )
    if 'buffered_bytes_size' in status:
        status['buffered_data'] = formatSize(status['buffered_bytes_size'])
        del status['buffered_bytes_size']
    if 'rows_written' in status:
        status['rows_written'] = formatCount(status['rows_written'])
    if 'bytes_written' in status:
        status['size_written'] = formatSize(status['bytes_written'])
        del status['bytes_written']
    if 'ignored_row_count' in status:
        status['ignored_row_count'] = formatCount(status['ignored_row_count'])
    if 'row_count_skew' in status:
        status['row_count_skew'] = formatCount(status['row_count_skew'])
    if 'min_shard_row_count' in status:
        status['min_shard_row_count'] = (
            formatCount(status['min_shard_row_count'])
        )
    if 'max_shard_row_count' in status:
        status['max_shard_row_count'] = (
            formatCount(status['max_shard_row_count'])
        )
    return status

def parseCmd(argv):
    """
    Parse command line arguments.
    Args:
        argv (list): List of command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Load data into Thoughtspot cluster using data importer '
                    'REST service.')
    parser.add_argument(
        '--cluster_host', default='localhost',
        help='URL of the ThoughtSpot cluster. Default is localhost.'
    )
    parser.add_argument(
        '--service_port', type=int, default=8442,
        help='Port on which dataload service is listening.'
    )
    parser.add_argument(
        '--username', required=True,
        help='Username to log in. Same as ThoughtSpot username. User must have '
             'ADMINISTRATION or DATAMANAGEMENT privilege to be able to load '
             'data.'
    )
    parser.add_argument(
        '--password',
        help='Password to log in. Same as ThoughtSpot password. User must have '
             'ADMINISTRATION or DATAMANAGEMENT privilege to be able to load '
             'data. This argument is optional because of sensitivity. If '
             'password is not provided as argument then user will be prompted '
             'to enter password in stdin.'
    )
    parser.add_argument(
        '--target_database', required=True,
        help='Name of target database.'
    )
    parser.add_argument(
        '--target_schema', default='falcon_default_schema',
        help='Name of target schema.'
    )
    parser.add_argument(
        '--target_table', required=True,
        help='Name of target table.'
    )
    parser.add_argument(
        '--source_files', nargs='+', required=True,
        help='Space separated list of files containing source data.'
    )
    parser.add_argument(
        '--max_ignored_rows', type=int,
        help='If number of ignored rows exceeds this limit, load is aborted.'
    )
    parser.add_argument(
        '--empty_target', dest='empty_target', action='store_true',
        help='When set, current rows in target table or file are dropped '
             'before loading new data.'
    )
    parser.set_defaults(empty_target=False)
    parser.add_argument(
        '--validate_only', dest='validate_only', action='store_true',
        help='Used for validating the input. The loader will do everything, '
             'short of commiting data to Falcon.'
    )
    parser.set_defaults(validate_only=False)
    parser.add_argument(
        '--file_target_dir',
        help='If a valid path is given, instead of writing the data to '
             'falcon manager, a DML file with the name <cycle_id>.dml will be '
             'created under the given path.'
    )
    parser.add_argument(
        '--type', choices=['CSV', 'DELIMITED', 'INTERNAL'],
        help='When non empty, represents type of source file. It can be CSV or '
             'DELIMITED or INTERNAL.'
    )
    parser.add_argument(
        '--field_separator',
        help='Applies to both CSV and DELIMITED, character that is used to '
             'split record into fields e.g., comma.'
    )
    parser.add_argument(
        '--trailing_field_separator', dest='trailing_field_separator',
        action='store_true',
        help='When set, all rows including the header (if applicable) have a '
             'trailing field separator otherwise the row would be considered '
             'as invalid row.'
    )
    parser.set_defaults(trailing_field_separator=False)
    parser.add_argument(
        '--enclosing_character',
        help='String representing enclosing character in CSV source format. '
             'This option is ignored for other source types.'
    )
    parser.add_argument(
        '--escape_character',
        help='String representing escape character in source data. This '
             'applies only for DELIMITED data format. This option is ignored '
             'for other data sources.'
    )
    parser.add_argument(
        '--null_value',
        help='String that represents null values in input e.g., empty.'
    )
    parser.add_argument(
        '--has_header_row', dest='has_header_row', action='store_true',
        help='When set, input data file should have header row.'
    )
    parser.set_defaults(has_header_row=False)
    parser.add_argument(
        '--flexible', dest='flexible', action='store_true',
        help='When set, attempts to load as follows. If extra columns are '
             'present in input file, these are discarded. If fewer columns are '
             'present in input file, missing columns are filled with nulls. '
             'Otherwise, load proceeds if input data file exactly matches '
             'target schema.'
    )
    parser.set_defaults(flexible=False)
    parser.add_argument(
        '--date_converted_to_epoch', dest='date_converted_to_epoch',
        action='store_true',
        help='Whether date and time fields are already converted to epoch in '
             'CSV source format. This option is ignored for other source types.'
    )
    parser.set_defaults(date_converted_to_epoch=False)
    parser.add_argument(
        '--date_time_format',
        help='String that describes format of date time field (specificied in '
             'strptime library) e.g., %%Y%%m%%d %%H:%%M:%%S to represent '
             '20011230 01:15:12.'
    )
    parser.add_argument(
        '--date_format',
        help='String that describes format of date field (specificied in '
             'strptime library) e.g., %%Y%%m%%d to represent 20011230.'
    )
    parser.add_argument(
        '--time_format',
        help='String that describes format of time field (specificied in '
             'strptime library) e.g., %%H:%%M:%%S to represent 01:15:12.'
    )
    parser.add_argument(
        '--second_fraction_start',
        help='Must be a single character and identifies beginning character of '
             'fractional component of seconds. Typical value is \".\", in '
             'other locales it can be \",\". This applies only when '
             '--skip_second_fraction is set.'
    )
    parser.add_argument(
        '--skip_second_fraction', dest='skip_second_fraction',
        action='store_true',
        help='When set, skip fractional part of seconds e.g., milliseconds, '
             'microseconds or nanoseconds from datetime or time values if '
             'present in source data. This option is ignored for other source '
             'types. Note that skipping fractional component (e.g. ms) from '
             'input data can impact upsert behavior if input data has '
             'non-unique fractional values for same time or datetime values.'
    )
    parser.set_defaults(skip_second_fraction=False)
    parser.add_argument(
        '--use_bit_boolean_values', dest='use_bit_boolean_values',
        action='store_true',
        help='When set, source CSV uses a bit for boolean values. Here in '
             'source false is represented as 0x0 and true as 0x1. If false, '
             'boolean values are interpreted using true_format and '
             'false_format. This option is ignored for other source types.'
    )
    parser.set_defaults(use_bit_boolean_values=False)
    parser.add_argument(
        '--true_format',
        help='String that represents True for boolean values in input.'
    )
    parser.add_argument(
        '--false_format',
        help='String that represents False for boolean values in input.'
    )
    args = parser.parse_args(argv[1:])
    return args

def main(argv):
    """
    Trigger data load using arguments provided in command line.
    Args:
        argv (list): List of command line arguments.
    """
    start_time = time.time()
    args = parseCmd(argv)
    base_hostport = args.cluster_host + ':' + str(args.service_port)
    if args.password is None:
        args.password = getpass('Password for user ' + args.username + ': ')
    # Start of the real load operation
    session = requests.Session()
    # 1. Login
    login(session, base_hostport, args.username, args.password)
    # 2. Startload
    load_hostport, cycle_id = startLoad(session, base_hostport,
                                        makeLoadParams(args))
    # 2a. [Nice to have] Get the load parameters that was sent to the server to
    #      validate/debug
    response = getLoadParams(session, base_hostport, cycle_id)
    load_params = response.json()['load_params']
    # 3. In case we have an internal-TSLoad-loadbalancer we will need the next
    #    two lines.
    if load_hostport != base_hostport:
        login(session, load_hostport, args.username, args.password)
    # 4. We can load the data (to the same db-schema-table), in multiple chunks.
    #    In this example, we are assuming each chunk is saved in different files
    #    and we call load on each of these files.
    #    This will just ingest the data and getStatus can be called anytime
    #    in between to get the actual status or any parsing errors etc.
    for file_name in args.source_files:
        load(session, load_hostport, cycle_id, file_name)
    # 5. Finaly, calling commitLoad will request the TS to commit the ingested
    #    data so far. Again, this just issues the request and returns.
    #    Commit will happen asynchronously and the status can be monitored
    #    through getStatus.
    commitLoad(session, load_hostport, cycle_id)
    # 6. Now that we have finished committing, we keep callign getStatus to
    #    know the status of the load.
    get_bad_records = False
    status = None
    while True:
        print('Will fetch status of load after 10 sec')
        time.sleep(10)
        response = None
        try:
            response = getStatus(session, load_hostport, cycle_id)
        except Exception as e:
            print('getStatus failed with exception:', str(e))
            continue
        try:
            status = response.json()
            # 6a. We check the ignored row counts to see if we need to fetch
            #     the bad records from the server.
            #     Also, if there are ignored rows, there'll be parsing errors
            #     as part of the getStatus that one can view to see the exact
            #     error.
            get_bad_records = (int(status['ignored_row_count']) > 0)
            if (status['internal_stage'] == 'DONE'
                    or ('status' in status
                        and 'code' in status['status']
                        and status['status']['code'] != 'OK')):
                print('Final load status:')
                pprint.pprint(AlterStatus(status))
                print('Load Params:')
                pprint.pprint(load_params)
                break
            print('Load is in progress.')
        except Exception as e:
            print('Failed to parse status response:', response.text)
            print('Error:', str(e))
    if get_bad_records:
        # 6b. If we have bad records, we send a request to the server to
        #     fetch those records.
        response = getBadRecords(session, load_hostport, cycle_id)
        print('Bad records response:\n', response.text)
    time_taken = time.time() - start_time
    time_unit = 'seconds'
    if time_taken > 60:
        time_taken = time_taken / 60
        time_unit = 'minutes'
    if time_taken > 60:
        time_taken = time_taken / 60
        time_unit = 'hours'
    print('Time taken:', '%.2f' % time_taken, time_unit)

if __name__ == '__main__':
    main(sys.argv)
