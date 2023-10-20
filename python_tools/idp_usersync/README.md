# User Sync Script

This Python script is designed to synchronize user data between an Identity Provider (IDP) and ThoughtSpot system.
Presently this supports deleting deactivated IDP users from ThoughtSpot

- [Preconditions](#Preconditions)
- [Usage](#Usage)
- [Arguments](#Arguments)
- [Script Break Down](#Script_Break_Down)
- [Summary Reporting](#Summary_Reporting)

## Preconditions

1. Python 3.x installed.
2. Necessary Python libraries installed. You can install them using `pip` if not already installed.
3. Setting `tscli --adv service add-javaopt tomcat.tomcat D orion.oktaMigrationCompleted true` on 
IAMv2 clusters for Login Api.


## Usage

Run the script with the following command:

```bash
python remove_deactivated_users.py --idp_domain [IDP_DOMAIN] --api_token [API_TOKEN] --system_url [SYSTEM_URL] --admin_username [ADMIN_USERNAME] --admin_password [ADMIN_PASSWORD] [--dry_run] [--debug]
```


## Arguments
1. `idp_domain`: The domain of the Identity Provider (e.g., dev-30114762.okta.com).
2. `api_token`: The API token for the Identity Provider.
3. `system_url`: The URL of the ThoughtSpot system. (e.g., https://test.thoughtspot.cloud)
4. `admin_username`: The username of the ThoughtSpot admin.
5. `admin_password`: The password of the ThoughtSpot admin.
6. `dry_run` (optional): If provided, the script will run in dry run mode without performing actual deletions.
7. `debug` (optional): If provided, the script will generate debug logs.


## Script Break Down
1. Fetches deactivated users from the IDP using the provided domain and API token.
2. Performs a system login to obtain a session for the ThoughtSpot system.
3. Searches for deactivated users in the ThoughtSpot system.
4. Deletes the identified users from ThoughtSpot.

From the deactivated users response from IDP we by default read `Login` property for the user to match 
it's username in ThoughtSpot. Make sure to change it if other property is used as username. 

##### Sample IDP User Response

```json
{
'id': '00uale3i9hojMDW0C5d7',
'status': 'DEPROVISIONED',
'created': '2023-07-31T08:11:10.000Z',
'activated': '2023-07-31T08:11:10.000Z',
'statusChanged': '2023-10-17T10:38:43.000Z',
'lastLogin': '2023-08-02T10:59:40.000Z',
'lastUpdated': '2023-10-17T10:38:43.000Z',
'passwordChanged': '2023-07-31T08:11:10.000Z',
'type': {
 'id': 'oty6x94qtnnZUtt1H5d7'
},
'profile': {
 'firstName': 'saml',
 'lastName': 'user',
 'mobilePhone': None,
 'secondEmail': None,
 'login': 'samluser@gmail.com',
 'email': 'samluser@gmail.com'
},
'credentials': {
 'emails': [
   {
     'value': 'samluser@gmail.com',
     'status': 'VERIFIED',
     'type': 'PRIMARY'
   }
 ],
 'provider': {
   'type': 'OKTA',
   'name': 'OKTA'
 }
},
'_links': {
 'self': {
   'href': 'https://<domain>/api/v1/users/<app_id>'
 }
}
}
```

## Summary Reporting

The script will generate log files with details about the synchronized users and any errors encountered. 
The logs will be stored in files named `user_sync_report_[timestamp].log` or `user_sync_report_dryrun_[timestamp].log` depending on whether dry run mode is used.