import argparse
import sys
import logging
from datetime import datetime
from collections import defaultdict
import requests

TS_LOGIN_ENDPOINT = "callosum/v1/tspublic/v1/session/login"
TS_USER_ENDPOINT = "callosum/v1/tspublic/v1/user"

# Function to fetch deactivated users from IDP
def fetch_deactivated_users(idp_domain, idp_api_token):
    print("Fetching deactivated users from IDP...")
    logging.info("Fetching deactivated users from IDP...")
    okta_base_url = f"https://{idp_domain}/api/v1"
    okta_deactivated_users_url = f"{okta_base_url}/users?filter=status+eq+%22DEPROVISIONED%22"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"SSWS {idp_api_token}"
    }
    response = requests.get(okta_deactivated_users_url, headers=headers)
    logging.debug("Fetch Deactivated users response: %s", response.text)
    if response.status_code == 200:
        logging.info("Successfully fetched deactivated users from IDP.")
        return response.json()

    print("Failed to fetch deactivated users from IDP.")
    logging.error("Failed to fetch deactivated users from IDP. Response: %s",
                  response.status_code)
    return None

# Function to perform system login and obtain JSESSIONID
def system_login(system_url, username, password):
    print("Attempting login to ThoughtSpot system...")
    logging.info("Attempting login to ThoughtSpot system...")
    login_url = f"{system_url}/{TS_LOGIN_ENDPOINT}"
    login_payload = {
        "username": username,
        "password": password,
        "rememberme": "true"
    }
    login_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    login_response = requests.post(login_url, data=login_payload, headers=login_headers)
    logging.debug("Login response: %s", login_response.text)
    if login_response.status_code == 204:
        jsessionid = login_response.headers.get("Set-Cookie")
        jsessionid = jsessionid.split("=")[1].split(";")[0]
        logging.info("Login to ThoughtSpot Successful")
        return jsessionid

    print("Failed to Login to ThoughtSpot")
    logging.error("Failed to Login to ThoughtSpot. Response: %s",
                  login_response.status_code)
    sys.exit(1)

# Function to search for users in the system
def search_users_in_system(system_url, jsessionid, user_list):
    print("Searching for deactivated users in the system...")
    logging.info("Searching for deactivated users in the system...")
    user_name_to_id_map = defaultdict(lambda: None)
    for user in user_list:
        user_search_url = f"{system_url}/{TS_USER_ENDPOINT}?name={user}&orgScope=ALL"
        user_search_headers = {
            "Cookie": f"JSESSIONID={jsessionid}"
        }
        user_search_response = requests.get(user_search_url, headers=user_search_headers)
        logging.debug("Search user response: %s", user_search_response.text)
        if user_search_response.status_code == 200:
            user_data = user_search_response.json()
            user_id = user_data.get("header", {}).get("id")
            if user_id:
                user_name_to_id_map[user] = user_id
        else:
            logging.warning("Failed to search for %s user in ThoughtSpot", user)

    return user_name_to_id_map

# Function to delete users in the system
def delete_users(system_url, jsessionid, user_name_to_id_map):
    print("Deleting users in the system...")
    logging.info("Deleting users in the system...")
    failed = []
    for user_name in user_name_to_id_map.keys():
        delete_user_url = f"{system_url}/{TS_USER_ENDPOINT}/" \
                          f"{user_name_to_id_map[user_name]}?orgScope=ALL"
        delete_user_headers = {
            "Cookie": f"JSESSIONID={jsessionid}"
        }
        delete_user_response = requests.delete(delete_user_url, headers=delete_user_headers)
        logging.debug("Delete User response: %s", delete_user_response.text)
        if delete_user_response.status_code == 204:
            logging.info("%s User Deleted", user_name)
        else:
            failed.append(user_name)
            logging.error("Failed to delete %s user. Response: %s", user_name,
                          delete_user_response.status_code)
    return failed

def main(args):

    # Fetch deactivated users from IDP
    deactivated_users = fetch_deactivated_users(args.idp_domain, args.api_token)
    if not deactivated_users:
        print("No deactivated users found in IDP to process.")
        logging.info("No deactivated users found in IDP to process.")
        sys.exit(1)

    # Set this to username for SSO users
    deactivated_users_login = [user['profile']['login'] for user in deactivated_users]
    logging.info("List of deactivated users: %s", deactivated_users_login)

    # Perform system login to obtain JSESSIONID
    jsessionid = system_login(args.system_url, args.admin_username, args.admin_password)

    if not jsessionid:
        sys.exit(1)

    # Search for users in the system
    user_name_to_id_map = search_users_in_system(args.system_url,
                                 jsessionid, deactivated_users_login)

    if len(user_name_to_id_map.keys()) < 1:
        print("No users found in the system to delete.")
        logging.info("No users found in the system to delete.")
        sys.exit(1)

    logging.info("Following users will be deleted from ThoughtSpot: %s",
                 list(user_name_to_id_map.keys()))

    if args.dry_run:
        print("Refer log file to see which users will be deleted from ThoughtSpot")
        sys.exit(0)

    # Delete users from TS
    failed = delete_users(args.system_url, jsessionid,
                               user_name_to_id_map)
    deleted_users = len(user_name_to_id_map.keys()) - len(failed)

    print(f"Deleted {deleted_users} user(s)")
    logging.info("Deleted %s users", deleted_users)

    if len(failed) > 0:
        print("Failed to delete %s users", len(failed))
        logging.info("Failed to delete %s users", failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to remove IDP deactivated users from ThoughtSpot.")
    parser.add_argument("--idp_domain",
        required=True, help="IDP domain (e.g., dev-30114762.okta.com)")
    parser.add_argument("--api_token", required=True, help="API token")
    parser.add_argument("--system_url", required=True, help="ThoughtSpot URL")
    parser.add_argument("--admin_username", required=True, help="ThoughtSpot admin username")
    parser.add_argument("--admin_password", required=True, help="ThoughtSpot admin password")
    parser.add_argument("--dry_run", action="store_true", help="Run in dry run mode")
    parser.add_argument("--debug", action="store_true", help="Get debug logs")

    arguments = parser.parse_args()

    # Configure logging
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_filename = f"user_sync_report_{timestamp}.log"
    if arguments.dry_run:
        log_filename = f"user_sync_report_dryrun_{timestamp}.log"

    logger = logging.getLogger()
    if arguments.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename)
    if arguments.debug:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)

    # Create a log formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    main(arguments)
