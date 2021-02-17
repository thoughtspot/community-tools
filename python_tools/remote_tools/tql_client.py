#!/usr/bin/env python3
# Copyright: ThoughtSpot Inc 2020
"""
This client can be used to establish a network connection with the
HTTP Server over an HTTPS channel. This client is used to send and
TQL commands/queries and receive response from the server. It is featured
with auto completion. The tokens for autocompletion are obtained
from the server.
"""
import argparse
from getpass import getpass
import itertools
import json
import os
import readline
import sys
import urllib
import urllib3

import requests
from tqdm import tqdm

# disable warnings due to verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OS X uses libedit
# force emacs bindings and add auto complete on tab
if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind -e")
    readline.parse_and_bind("bind '\t' rl_complete")
else:
    readline.parse_and_bind("tab: complete")


class TQLCompleter():
    """
    This class is used to enable autocomplete for tql.
    """
    def __init__(self, tokens):
        # Tokens is a dictionary of autocomplete words
        self.tokens = tokens

    def complete(self, text, state):
        """
        Function for autocomplete's completion logic.
        a. Case-sensitive autocompletion for "schema" tokens.
        b. Case-insensitive autocompletion for language token.
        c. For case-insensitive autocompletion, case for returned word depends
        on the currently typed last character.
        d. Take all language tokens and if less than 30, remaining schema tokens
        """
        results = []
        token_count = 30
        if 'language' in self.tokens:
            if text[-1].islower():
                results += list(itertools.islice([x.lower() + " " for x in \
                    self.tokens['language'] if x[:len(text)].lower() ==\
                    text.lower()], token_count))
            else:
                results += list(itertools.islice([x.upper() + " " for x in \
                    self.tokens['language'] if x[:len(text)].upper() ==\
                    text.upper()], token_count))
        if 'schema' in self.tokens:
            results += list(itertools.islice([x + " " for x in \
                    self.tokens['schema'] if x[:len(text)] == text],
                                             token_count - len(results)))
        results += [None]
        return results[state]

    def update(self, new_tokens):
        """
        Function to update/append autocomplete tokens.
        a. If key(schema/language) is already present, it overwrites value(list)
        b. If key is not present, it is added to the tokens dictionary.
        """
        for key, val in new_tokens.items():
            self.tokens[key] = val

    def initializeAutoComplete(self):
        """
        Function to pass 'complete' function to readline's set_completer
        """
        readline.set_completer(self.complete)


class RequestTQL():
    """
    Class to initialize the request object and send requests to the server.
    a. request purpose denotes one of the following purposes:
    tokens-static, tokens-dynamic, query or script.
    b. args: argv (list): List of command line arguments.
    """
    def __init__(self, url, session=None, session_id=None,\
                 headers=None, data=None, files=None, args=None):
        self.content = {'data':data, 'file':files}
        self.args = args
        self.session = session
        self.url = url
        if bool(headers):
            self.headers = headers
        else:
            self.headers = {'Content-Type':'text/plain', 'X-Requested-By':
                            'ThoughtSpot', 'JSESSION_ID':session_id}
        self.question_id = [] # used for interactive questions only
        self.bar_dict = {} # used for progress bar only

    def show(self):
        """
        Function to show the contents of the request
        """
        print('')
        print('url:', self.url)
        print('headers:', self.headers)
        print('data:', self.content['data'])
        print('files:', self.content['file'])
        print('')

    def getTokens(self):
        """
        Function to get tokens from the server. get request used to get tokens.
        b. static tokens are added under "language" key
        c. dynamic tokens are added under "schema" key
        """
        response = None
        try:
            response = self.session.get(url=self.url, data=self.content['data'],
                                        headers=self.headers, verify=False)
            # No Authorization Response code
            if response.status_code == 401:
                print("No Authorization to run tql.")
                sys.exit(1)
            if response.status_code // 100 != 2: # 2xx response code
                raise Exception('Autocomplete tokens could not be fetched.'
                                + 'Response: ' + response.text + '. url: '
                                + self.url)
        except Exception as e:
            if self.args.debug:
                print('Get request failed with exception:', str(e))
            return {}
        return list(response.json()['tokens'])

    def __printResponse(self, resp_json):
        """
        Helper function for runQuery
        a. This function prints the response message to stdout
        b. Whole response gets printed in case debug flag is True
        """
        if self.args.debug:
            print(resp_json)
        else:
            try:
                table = resp_json['result']['table']
                headers = table['headers']
                header_line = []
                for header in headers:
                    header_line.append(header['name'])
                header_line = "|".join(header_line)
                print(header_line)
                print("-" * len(header_line))
                rows = table['rows']
                for row in rows:
                    row_line = row['v']
                    print("|".join(row_line))
            except KeyError:
                pass
            try:
                for message in resp_json['result']['message']:
                    message_type = message['type']
                    value = message['value']
                    terminator = '\n'
                    if value.endswith('\n'):
                        terminator = ''
                    if message_type == 'ERROR':
                        print(value, end=terminator)
                    elif message_type == 'INFO':
                        print(value, end=terminator)
                    else:
                        print(value, end=terminator)
            except KeyError:
                pass

    def __showProgress(self, resp_json):
        """
        Helper function for runQuery to show progress bar
        Each progress element must have percent and label
        """
        for progress in resp_json['result']['progress']:
            label = None
            percent = None
            details = ""
            bar_id = None
            try:
                label = progress['label']
            except KeyError:
                continue
            try:
                bar_id = progress['id']
            except KeyError:
                continue
            try:
                percent = int(progress['percentage'])
            except KeyError:
                continue
            try:
                details = progress['details']
            except KeyError:
                pass
            if bar_id not in self.bar_dict:
                # Create tqdm object if not present for the current bar_id
                # Each element of bar_dict is a list
                # The first element of list is tqdm object and the second
                # denotes the progress so far.
                self.bar_dict[bar_id] = [tqdm(total=100, leave=False,
                                              file=sys.stdout), 0]
            # Update function takes the incremental value
            self.bar_dict[bar_id][0].update(percent - self.bar_dict[bar_id][1])
            self.bar_dict[bar_id][0].set_description(desc=details + " " + label)
            self.bar_dict[bar_id][0].refresh()
            self.bar_dict[bar_id][1] = percent
        # Close all progress bars in case query execution is complete
        if 'complete' in resp_json['result']:
            for bar_id in self.bar_dict:
                self.bar_dict[bar_id][0].close()
            self.bar_dict = {}

    def __promptResp(self, resp_json):
        """
        Helper function for runQuery to get prompt answers from user
        a. It updates self.content['data'] with user answers to be send in next
        request.
        b. self.question_id list contains already asked questions for the
        current query.
        """
        if 'prompt_responses' not in self.content['data']['query']:
            self.content['data']['query']['prompt_responses'] = []
        for question in resp_json['result']['interactive_question']:
            answered = False
            ans = None
            try:
                while not answered:
                    if question['question_id'] not in self.question_id:
                        self.question_id.append(question['question_id'])
                        print(question['banner'])
                    ans = input(question['prompt'] + '\n').strip()
                    answered = True
                    if 'options' in question:
                        if ans not in question['options']:
                            answered = False
            except KeyError:
                pass
            if answered:
                resp = {'question_id':question['question_id'], 'answer':ans}
                self.content['data']['query']['prompt_responses'].append(resp)


    def runQuery(self):
        """
        Function to run a single query or a script via post request.
        a. It prints the response received from the server
        b. Returns the new context ({} if no new context provided by the server)
        """
        response = None
        new_context = {}
        data = None
        print('running statement...', end='', flush=True)
        try:
            if self.content['data'] is not None:
                data = json.dumps(self.content['data'])
            response = self.session.post(url=self.url, data=data,
                                         files=self.content['file'],
                                         headers=self.headers,
                                         verify=False, stream=True)
            if response.status_code // 100 != 2: # 2xx response code
                raise Exception('Statement Execution failed. Response: '
                                + response.text + '. url: ' + self.url)
        except Exception as e:
            print('Post request failed with exception:', str(e))
            return {}
        # clear the current line
        sys.stdout.write('\033[2K\033[1G')
        # currently, there is a tight coupling of each result coming as new line
        # TODO (revisit this later)
        resp_json = {}
        for line in response.iter_lines(decode_unicode=True):
            try:
                if line:
                    # Decode UTF-8 bytes to Unicode, and convert single quotes
                    # to double quotes to make it valid JSON
                    #resp_json = line.decode('utf8').replace("'", '"')
                    resp_json = line.decode('utf8').replace("\'", "'")
                    resp_json = json.loads(resp_json)
                    # In case of script, just keep printing the response
                    if bool(self.args.file):
                        self.__printResponse(resp_json)
                        continue
                    # Show Progress bar
                    if 'progress' in resp_json['result']:
                        self.__showProgress(resp_json)
                        sys.stdout.flush()
                    # Handle Interactive Questions
                    if 'interactive_question' in resp_json['result']:
                        self.__promptResp(resp_json)
                        return self.runQuery()
                    # Store final context (if received)
                    try:
                        new_context = resp_json['result']['final_context']
                    except KeyError:
                        pass
                    # Print response message
                    self.__printResponse(resp_json)
                    # Actually loop breaks automatically when the connection
                    # is closed. This is an additional check.
                    # break streaming loop if execution is completed
                    if 'complete' in resp_json['result']:
                        break
            except Exception as e:
                print("Unable to process response. Error: " + str(e))
        return new_context

def addQueryOptions(args):
    """
    Function to add Query Options.
    """
    # Query Options
    query_options = {}
    if args.query_results_apply_top_row_count is not None:
        query_options["query_results_apply_top_row_count"] = \
        args.query_results_apply_top_row_count
    if args.query_row_count_only is not None:
        query_options["query_row_count_only"] = args.query_row_count_only
    query_options["pagination"] = {}
    if args.start is not None:
        query_options["pagination"] = {"start":args.start}
    if args.size is not None:
        query_options["pagination"] = {"size":args.size}
    return query_options

def addFormattingOptions(args):
    """
    Function to add Formatting Options.
    """
    # Formatting Options
    formatting_options = {}
    if args.field_separator is not None:
        formatting_options["field_separator"] = args.field_separator
    if args.row_separator is not None:
        formatting_options["row_separator"] = args.row_separator
    if args.null_string is not None:
        formatting_options["null_string"] = args.null_string
    date_formatting = {}
    if args.date_format is not None:
        date_formatting["date_format"] = args.date_format
    if args.date_time_format is not None:
        date_formatting["date_time_format"] = args.date_time_format
    if args.time_format is not None:
        date_formatting["time_format"] = args.time_format
    if args.format_date_as_epoch is not None:
        date_formatting["format_date_as_epoch"] = args.format_date_as_epoch
    formatting_options["date_format"] = date_formatting
    return formatting_options

def addScriptingOptions(args):
    """
    Function to add scripting options.
    """
    scripting_opt = {}
    if args.add_database is not None:
        scripting_opt["add_database"] = args.add_database
    if args.script_comments is not None:
        scripting_opt["script_comments"] = args.script_comments
    if args.script_extensions is not None:
        scripting_opt["script_extensions"] = args.script_extensions
    if args.script_guids is not None:
        scripting_opt["script_guids"] = args.script_guids
    if args.script_parsing_hints is not None:
        scripting_opt["script_parsing_hints"] = args.script_parsing_hints
    if args.script_schema_versions is not None:
        scripting_opt["script_schema_versions"] = args.script_schema_versions
    return scripting_opt

def addAdvancedOptions(args):
    """
    Function to add advanced options
    """
    adv_opt = {}
    if args.input_row_size_fetch_max_rows is not None:
        adv_opt["input_row_size_fetch_max_rows"] = \
        args.input_row_size_fetch_max_rows
    if args.use_jit is not None:
        adv_opt["use_jit"] = args.use_jit
    if args.skip_cache is not None:
        adv_opt["skip_cache"] = args.skip_cache
    if args.progress_wrapper_timeout_sec is not None:
        adv_opt["progress_wrapper_timeout_sec"] = \
        args.progress_wrapper_timeout_sec
    if args.offlining_during_resharding_default is not None:
        adv_opt["offlining_during_resharding_default"] = \
        args.offlining_during_resharding_default
    if args.use_postgres_sql_parser is not None:
        adv_opt["use_postgres_sql_parser"] = args.use_postgres_sql_parser
    if args.generate_guids_in_ddl is not None:
        adv_opt["generate_guids_in_ddl"] = args.generate_guids_in_ddl
    if args.allow_unsafe is not None:
        adv_opt["allow_unsafe"] = args.allow_unsafe
    if args.continue_execution_on_error is not None:
        adv_opt["continue_execution_on_error"] = \
        args.continue_execution_on_error
    return adv_opt

def addOptions(args):
    """
    Function to add options.
    """
    options = {}
    options["query_options"] = addQueryOptions(args)
    options["formatting_options"] = addFormattingOptions(args)
    options["scripting_options"] = addScriptingOptions(args)
    options["adv_options"] = addAdvancedOptions(args)
    return options

def createRequest(context, request_purpose, args, session, session_id,
                  url_map, script, query):
    """
    Function to create and return the RequestTQL object for running either
    a single query or a script.
    """
    url = getUrl(url_map, request_purpose)
    data = {}
    data["context"] = context
    data["options"] = addOptions(args)
    if bool(args.file):
        # Script types
        tql_script = 1
        server_script = 2
        if request_purpose == "server_script":
            data["script_type"] = server_script
        else:
            data["script_type"] = tql_script
        data["script"] = script
    else:
        # If request purpose is not 'script', then it will be 'query'
        data["query"] = {"statement":query}
    return RequestTQL(session=session, session_id=session_id, url=url,
                      args=args, data=data)

def readInput(context):
    """
    Function to read input from the prompt with ';' at the end of line
    indicating the query is completely written.
    a. exit /quit / ctrl-d are used to come out of prompt
    """
    if 'database' in context and context['database'] != '':
        database = context['database']
    else:
        database = '(none)'
    try:
        query = input('TQL [database=' + database + ']> ').strip()
        while (query == '' or query[-1] != ';') and query.strip() \
               not in ['exit', 'quit', 'help', 'h']:
            line = input('> ').strip()
            query += ' ' + line
    except EOFError: # Catch the ctrl-d
        print('')
        return ''
    except KeyboardInterrupt: # Catch the ctrl-c
        print('')
        return readInput(context)
    return query.strip()

def printInitials(host):
    """
    Function to print initials.
    a. It should be called just before the tql prompt starts.
    """
    print("Welcome to ThoughtSpot SQL command line interface.\n"
          "Press Control-C to clear current command.\n"
          "Press Control-D or enter exit; or quit; to exit.\n"
          "Enter help or h; or help; for available commands.\n\n"
          "Connected to remote TQL service.\n"
          "Cluster address : ", host, "\n")

def tqlPrompt(context, args, session, session_id, url_map, completer):
    """
    This function implements the interactive shell logic.
    """
    # print Initials
    printInitials(host=args.host)
    query = ''
    while True:
        get_dynamic_token = False
        try:
            query = readInput(context)
        except Exception as e:
            print("Failed to get input. Error: ", str(e))
            return
        if query != '' and query not in ['quit', 'exit', 'quit;', 'exit;']:
            # In case of help;, h;, h or help, show usage
            if query in ['h', 'help', 'help;', 'h;']:
                showUsage()
                continue
            # create a RequestTQL object to run the input query
            request_purpose = "query"
            query_tql = createRequest(context, request_purpose, args,
                                      session, session_id, url_map, None, query)
            new_context = query_tql.runQuery()
            # Update context
            if 'database' in new_context:
                context['database'] = new_context['database']
            if 'server_schema_version' in new_context:
                context['server_schema_version'] = new_context['server_'\
                                                   'schema_version']
                get_dynamic_token = True
            # Update tokens (in case new server schema version is returned)
            if get_dynamic_token and args.autocomplete:
                # Get dynamic tokens from the server
                getDynamicTokens(session, session_id, completer, url_map, args)
        else:
            break

def getDynamicTokens(session, session_id, completer, url_map, args):
    """
    Function to update autocomplete with dynamic tokens
    a. It makes a http request to get dynamic tokens
    b. updates the received tokens in autocomplete
    """
    tokens = {}
    request_purpose = 'tokens-dynamic'
    url = getUrl(url_map, request_purpose)
    tokens_tql = RequestTQL(session=session, session_id=session_id, url=url,
                            args=args)
    tokens['schema'] = tokens_tql.getTokens()
    tokens['schema'].sort()
    # update autocomplete with dynamic tokens
    completer.update(tokens)

def getStaticTokens(session, session_id, completer, url_map, args):
    """
    Function to update autocomplete with static tokens
    a. It makes a http request to get static tokens
    b. updates the received tokens in autocomplete
    """
    tokens = {}
    request_purpose = 'tokens-static'
    url = getUrl(url_map, request_purpose)
    tokens_tql = RequestTQL(session=session, session_id=session_id, url=url,
                            args=args)
    tokens['language'] = tokens_tql.getTokens()
    tokens['language'].sort()
    # update auto completer with the received tokens.
    completer.update(tokens)

def getUrl(url_map, request_purpose):
    """
    Function to return url based on request purpose
    a. it performs a lookup on url_map
    """
    url = None
    if request_purpose in url_map:
        url = url_map[request_purpose]
    return url

def getUrlMap(args):
    """
    Function to return a map (request purpose:url)
    """
    url_map = {}
    # separate url for each request purpose
    url_map['server_script'] = "https://"+ args.host +\
        "/ts_dataservice/v1/public/tql/script"
    url_map['script'] = "https://"+ args.host +\
        "/ts_dataservice/v1/public/tql/script"
    url_map['tokens-static'] = "https://" + args.host +\
        "/ts_dataservice/v1/public/tql/tokens/static"
    url_map['tokens-dynamic'] = "https://" + args.host +\
        "/ts_dataservice/v1/public/tql/tokens/dynamic"
    url_map['query'] = "https://" + args.host +\
        "/ts_dataservice/v1/public/tql/query"
    return url_map

def getCredentials(username, password):
    """
    Function to get credentials (if not already provided via arguments)
    """
    try:
        if username is None:
            username = input('username: ')
        if password is None:
            password = getpass('Password for user ' + username + ': ')
    except EOFError: # Catch the ctrl-d
        print('')
        sys.exit(1)
    except KeyboardInterrupt: # Catch the ctrl-c
        print('')
        sys.exit(1)
    return username, password

def login(session, host, username, password):
    """
    Send login request to HTTP Server.
    Args:
        session (Session): Object to hold and persist session cookie.
        host: Domain name or IP address of the cluster
    User will be given three extra attempts in case of wrong user name/password
    """
    response = None
    try_count = 4
    while try_count > 0:
        username, password = getCredentials(username, password)
        json_data = urllib.parse.urlencode({'username':username,
                                            'password':password})
        headers = {'Content-type':'application/x-www-form-urlencoded',
                   'Accept':'application/json', 'X-Requested-By':'ThoughtSpot'}
        url = 'https://' + host + '/callosum/v1/session/login'
        response = session.post(url, data=json_data, headers=headers,
                                verify=False)
        # wrong credential response
        if response.status_code == 401:
            try_count -= 1
            print("Wrong Credentials! Try again! Retry Attempts left:",
                  try_count, "\n")
            password = None
            username = None
            continue
        if response.status_code // 100 != 2: # 2xx or 4xx response code
            raise Exception('login request failed. Response: ' + response.text)
        break
    if response is None or response.status_code == 401:
        print('Login Failed!')
        sys.exit(1)
    return response

def str2bool(arg_val):
    """
    Helper Function to ensure correct parsing of bool options.
    """
    if isinstance(arg_val, bool):
        return arg_val
    if arg_val.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if arg_val.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')

def parseCmd(argv):
    """
    Parse command line arguments.
    Args:
        argv (list): List of command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Execute TQL Statements.')
    # required arguments
    parser.add_argument(
        '--host', default=None,
        help='Domain name or IP address of the cluster. This is a required'
             ' argument.'
    )
    # optional arguments
    parser.add_argument(
        '--usage', default=False, action='store_true',
        help='Use --usage to get the list of basic tql commands.'
    )
    parser.add_argument(
        '--debug', type=str2bool, default=False,
        help='Use it to get the entire response printed on console. Default'
             ' value is false.'
    )
    parser.add_argument(
        '--username', default=None,
        help='username to log in. Same as ThoughtSpot username.'
             'If username is not provided as argument then user'
             'will be prompted to enter username in stdin.'
    )
    parser.add_argument(
        '--password', default=None,
        help='Password to log in. This argument is optional because of'
             'sensitivity. If password is not provided as argument then user'
             'will be prompted to enter password in stdin.'
    )
    parser.add_argument(
        '--file', default=None,
        help='Name of tql script file. Default value is None.'
    )
    parser.add_argument(
        '--schema', default=None,
        help='Schema name to use in case statements have empty schema.'
             ' Default value is falcon_default_schema.'
    )
    parser.add_argument(
        '--server_script', type=str2bool, default=False,
        help='Set this flag to true if the script provided is server schema'
             ' script. Default value is false.'
    )
    parser.add_argument(
        '--autocomplete', type=str2bool, default=True,
        help='Flag to toggle auto complete feature.'
             'When false, autocomplete feature will be turned off.'
             ' Default value is true.'
    )
    # Query Options - Pagination Options
    parser.add_argument(
        '--start', type=int, default=None,
        help='Offset to fetch query results from. Default is 0.'
             'When only result set row count is requested, then it is'
             'interpreted as number of rows after pagination_start.'
    )
    parser.add_argument(
        '--size', type=int, default=None,
        help='Batch size of a result. Default is 5000000.'
    )
    # Query Options
    parser.add_argument(
        '--query_results_apply_top_row_count', type=int, default=None,
        help='Limits number of rows returned from the server by adding'
             'a top condition to the query. Default value is 50.'
    )
    parser.add_argument(
        '--query_row_count_only', type=str2bool, default=None,
        help='Flag to only display row counts from query results,'
             ' otherwise displays whole results. Default value is false.'
    )
    # Formatting Options -- Date Format
    parser.add_argument(
        '--date_format', default=None,
        help='Format string for date values. Default is %%Y-%%m-%%d.'
    )
    parser.add_argument(
        '--date_time_format', default=None,
        help='Format string for date time values.'
        ' Default is %%Y-%%m-%%d %%H:%%M:%%S.'
    )
    parser.add_argument(
        '--time_format', default=None,
        help='Format string for time values. Default is %%H:%%M:%%S.'
    )
    parser.add_argument(
        '--format_date_as_epoch', type=str2bool, default=None,
        help='Use this flag to shows date, time and date time as epoch values.'
    )
    # Formatting Options
    parser.add_argument(
        '--field_separator', default=None,
        help='Separator between field values of a row. Default is |'
    )
    parser.add_argument(
        '--row_separator', default=None,
        help='Separator between rows. Default is \\n.'
    )
    parser.add_argument(
        '--null_string', type=str2bool, default=None,
        help='String to represent null values. Default is (null).'
    )
    # Scripting Options
    parser.add_argument(
        '--add_database', type=str2bool, default=None,
        help='Flag to add database name to fully qualify table names. Default'
             ' value is true.'
    )
    parser.add_argument(
        '--script_comments', type=str2bool, default=None,
        help='Flag to add scripts comments, otherwise comments are not added'
             ' to scripts. Default value is true.'
    )
    parser.add_argument(
        '--script_extensions', type=str2bool, default=None,
        help='When true, scripts extensions specific to our system e.g., fact,'
             ' dimension, parsing hint etc; otherwise ignores these extensions'
             ' from the generated script. Default value is true.'
    )
    parser.add_argument(
        '--script_guids', type=str2bool, default=None,
        help='When true, add guid information to generated script. Otherwise'
             ' guids are omitted from the script. Default value is false.'
    )
    parser.add_argument(
        '--script_parsing_hints', type=str2bool, default=None,
        help='When true, add date parsing hints to generated script. Otherwise'
             ' parsing hints are omitted from the script.'
             ' Default value is false.'
    )
    parser.add_argument(
        '--script_schema_versions', type=str2bool, default=None,
        help='When true, add live and max schema version to generated script.'
             ' Otherwise schema versions are omitted from the script.'
             ' Default value is false.'
    )
    # Advanced Options
    parser.add_argument(
        '--use_jit', type=str2bool, default=None,
        help='When true, may use jit for queries, otherwise does not jit'
             ' queryplan. Default value is true.'
    )
    parser.add_argument(
        '--skip_cache', type=str2bool, default=None,
        help='When true, the falcon results cache is skipped. Default value'
             ' is false.'
    )
    parser.add_argument(
        '--offlining_during_resharding_default', type=str2bool, default=None,
        help='When true, sets table offline during resharding operations. This'
             ' value is overridden by user input when user prompts are'
             ' displayed. Default value is false.'
    )
    parser.add_argument(
        '--use_postgres_sql_parser', type=str2bool, default=None,
        help='If set uses postgres sql parser. Default value is false.'
    )
    parser.add_argument(
        '--generate_guids_in_ddl', type=str2bool, default=None,
        help='If true, thoughtspot system generates guids for objects to be'
             ' created, otherwise guids are used from sql script specification.'
             ' Default value is true.'
    )
    parser.add_argument(
        '--allow_unsafe', type=str2bool, default=None,
        help='If true, allows certain unsafe commands to be executed.'
             ' Specifically if sharding keys are not included in primary key'
             ' of a table, currently primary key enforcement is not guaranteed'
             ' by the system. In this case caller if they know that input data'
             ' has unique rows for primary key, they can override system'
             ' behavior to still allow such schema to be generated.'
             ' Default value is false.'
    )
    parser.add_argument(
        '--continue_execution_on_error', type=str2bool, default=None,
        help='If true, continues to execute remaining sql statements in input'
             ' file in case of execution error. Otherwise sql statements'
             ' execution is terminated. Default value is true.'
    )
    parser.add_argument(
        '--input_row_size_fetch_max_rows', type=int, default=None,
        help='Limits number of rows that are fetched to estimate row size.'
             ' If zero or negative value is specified, all rows are queried.'
             'Default value is 10000.'
    )
    parser.add_argument(
        '--progress_wrapper_timeout_sec', type=int, default=None,
        help='Timeout for commands that report progress. This value overrides'
             ' the rpc_socket_timeout_sec flag. Commands involving resharding'
             ' and updating columns are currently affected. Default value is'
             ' 86400.'
    )
    args = parser.parse_args(argv[1:])
    return args

def showUsage():
    """
    Function to show usage for h, h;, help, or help; commands, or --usage option
    """
    print("tql is a command line interface for creating schemas "
          "and performing basic database administration.\n"
          "All commands MUST end with ;\n"
          "Commands can optionally be multi-line.\n"
          "Few common commands\n"
          "-----------------------\n"
          "show databases;       -> list all available databases\n"
          "use db;               -> switches context to specified database\n"
          "                         'db' this must be done if queries do\n"
          "                         not use full names (db.schema.table)\n"
          "                         for tables.\n"
          "show schemas;         -> list all schemas within current\n"
          "                         database (set by use db;)\n"
          "show tables;          -> list all tables within current\n"
          "                         database (set by use db;)\n"
          "show table tab;       -> list all columns for table 'tab'\n"
          "show views;           -> list all views within current\n"
          "                         database (set by use db;)\n"
          "show view vw;         -> list all columns for view 'vw'\n"
          "script server;        -> generates SQL for all databases\n"
          "script database db;   -> generates create SQL for all tables in\n"
          "                         database 'db'\n"
          "script table tab;     -> generates create SQL for table 'tab'\n"
          "create database db;   -> create database 'db'\n"
          "drop database db;     -> drop database 'db'\n"
          "create table tab ...; -> create table 'tab'. Example ...\n"
          "                         create table t1 (c1 int, c2 int);\n"
          "                         create table t2 (d1 int, d2 int,\n"
          "                         constraint primary key(d1));\n"
          "drop table tab;       -> drop table 'tab'\n"
          "alter table tab ...;  -> alter table 'tab'. Examples ...\n"
          "                         alter table t add column c int \n"
          "                         default 5;\n"
          "                         alter table t rename column c to d\n"
          "                         alter table t drop column c\n"
          "                         alter table t1 add constraint\n"
          "                         foreign key (c1, c2) references\n"
          "                         t2 (d1, d2);\n"
          "                         alter table t1 drop constraint foreign\n"
          "                         key t2;\n"
          "select from tab ...;  -> select query against the specified\n"
          "                         set of tables. Example queries:\n"
          "                         select TOP 10 c1 from t1;\n"
          "                         select c1, sum(c2) from tab1;\n"
          "                         select c11, sum(c22) as X from t1, t2\n"
          "                         where t11.c12 = t2.c21 and c13 = 10\n"
          "                         group by c11\n"
          "                         order by X desc\n"
          "                         select c1, sum(c2) from tab1 limit 10;\n"
          "insert into tab ...;  -> insert values into 'tab'\n"
          "update tab ...;       -> update rows in 'tbl' that match\n"
          "                         optionally provided predicates.\n"
          "                         Predicates are of form column = value\n"
          "                         connected by 'and' keyword. Set values\n"
          "                         in 'columns' to specified values.\n"
          "delete from tab ...;  -> delete rows from 'tbl' that match\n"
          "                         optionally provided predicates.\n"
          "                         Predicates are of form column = value\n"
          "                         connected by 'and' keyword.\n"
          "compact table tab;    -> compact table 'tab' data version\n"
          "                         chain to a single DML file.\n"
          "compact all_tables;    -> compact all tables in current db\n"
          "exit;                 -> exit.\n\n"
          "For a list of all commands, type \"help;\" after invoking tql\n")

def readScript(args):
    """
    Either args.file should contains the provided file name
    Or the script was passed through pipe
    """
    script = None
    # check input type (if piped or not)
    # is_pipe will be True if the input is piped
    is_pipe = not os.isatty(sys.stdin.fileno())
    if is_pipe:
        script = ""
        for line in sys.stdin:
            script = script + line
        args.file = True
        # Reopen stdin for further input
        sys.stdin.close()
        sys.stdin = os.fdopen(1)
    elif bool(args.file):
        with open(args.file, "r") as file_handler:
            script = file_handler.read()
    return script

def main(argv):
    """
    Main function to do stuff
    """
    # Parse arguments
    args = parseCmd(argv)
    # In case of usage option, show basic commands and exit from program
    if args.usage:
        showUsage()
        return
    # Check for the required argument
    # Separate checking required as Making required=True while parsing
    # doesn't allow to run with only --usage option
    if not bool(args.host):
        print("error: the following arguments are required: --host")
        return
    # Read script and reopen stdin (in case of piped input)
    # Returns file content as text string and None if no script is provided
    script = readScript(args)
    # Start session
    session = requests.Session()
    # Login and get JSESSION_ID
    session_id = ''
    try:
        response = login(session, args.host, args.username, args.password)
        session_id = response.json()['userGUID']
        print('Login Successful.\n')
    except Exception as e:
        print(str(e))
        return
    # Initialize context with initial schema version as -1
    context = {}
    if bool(args.schema):
        context['schema'] = args.schema
    context['server_schema_version'] = -1
    # Get url map (request purpose:url)
    url_map = getUrlMap(args)
    if script:
        request_purpose = "script"
        if args.server_script:
            request_purpose = "server_script"
        script_tql = createRequest(context, request_purpose, args, session,
                                   session_id, url_map, script, None)
        script_tql.runQuery()
    else:
        # interactive shell logic
        # 1. initialize auto complete
        completer = TQLCompleter({})
        completer.initializeAutoComplete()
        if args.autocomplete:
            # 1.a get all the static tokens
            getStaticTokens(session, session_id, completer, url_map, args)
            # 1.b get all the dynamic tokens
            getDynamicTokens(session, session_id, completer, url_map, args)
        # 2. Start tql prompt (quit, exit or ctrl-d are used to terminate)
        tqlPrompt(context, args, session, session_id, url_map, completer)

if __name__ == '__main__':
    main(sys.argv)
