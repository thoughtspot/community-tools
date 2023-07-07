# **Org Aware Ldap Script**


## Table of Contents

- [Usage]($Usage)
- [Flags](#Flags)
- [Validations](#Validations)
- [Script Break Down](#Script_Break_Down)
- [Summary Reporting](#Summary_Reporting)

## Usage
```shell
python3 syncUsersAndGroups.py script --ts_hostport TS_HOSTPORT --ts_uname TS_USERNAME --ts_pass TS_PASSWORD 
--disable_ssl --ldap_hostport LDAP_HOSTPORT --ldap_uname LDAP_USERNAME --ldap_pass LDAP_PASSWORD 
--basedn LDAP_BASEDN --filter_str FILTER_STR --include_nontree_members --sync --purge --debug 
--org_mapping --org_file_input ORG_FILE_INPUT_PATH --remove_user_orgs --remove_group_orgs --purge
```

## Flags

1. <b>org_mapping</b>: Add this flag to specify if the ldap sync needs to be org aware
2. <b>org_file_input</b>: Takes the path of the org mapping input json file which will 
   be used to populate objects org assignment <br/>
   Sample input file: <br/>
    ```json
   [
       {
       "dn": "CN=Enterprise Admins,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org1",
           "org2",
           "org3"
        ]
       },
       {
       "dn": "CN=tsadmin,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org1",
           "org2",
           "org3"
        ]
       }
   ]
   ```
3. <b> org_attr</b>: Flag to indicate that an <b>"org"</b> attribute is added in the ldap 
   user/group properties which will be used to populate objects org assignment. This attribute
   will have a list of org names to which the object belongs
4. <b>add_recursive_org_membership</b>: Flag to indicate that the org mapping of the parent will
   be recursively added to their members. Example:<br/>
    ```json
   [
       {
       "dn": "CN=Enterprise Admins,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org3"
        ]
       },
       {
       "dn": "CN=tsadmin,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org1"
        ]
       }
   ]
   ```
   "tsadmin" is a member of "Enterprise Admins". If we pass the <b>add_recursive_org_membership</b>
   flag, then tsadmin will be added to org3 as well i.e. to it's parent's org.
5. <b>purge</b>: Flag to delete users and groups from ThoughtSpot system which are not there
   in present sync or whose org list is empty.
6. <b>purge_users</b>: Flag to delete users from ThoughtSpot system which are not there
   in the present sync or whose org list is empty.
7. <b>purge_groups</b>: Flag to delete groups from ThoughtSpot system which are not there
   in the present sync or whose org list is empty.
8. <b>remove_user_orgs</b>: Flag to remove users from orgs which are not there in the present
    sync.
9. <b>remove_group_orgs</b>: Flag to remove groups from orgs which are not there in the present
   sync.

## Validations
1. If the <b>org_mapping</b> flag is added. The script will exit if none of <b>org_file_input</b>
   or <b>org_attr</b> flags are provided.
2. For any parent-member relationship, if the member doesn't exist in each of parent't org the script
   will throw org conflict, unless ni org mapping for the member is given. Example: <br/>
   Case1:
    ```json
   [
       {
       "dn": "CN=Enterprise Admins,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org3"
        ]
       },
       {
       "dn": "CN=tsadmin,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org1"
        ]
       }
   ]
   ```
   and <b>add_recursive_org_membership</b> flag is not added.<br/>
   The script will throw an Org Conflict error between tsadmin member and Enterprise Admins parent<br/>
   Case2:
   ```json
   [
       {
       "dn": "CN=Enterprise Admins,CN=Users,DC=ldap,DC=thoughtspot,DC=com",
       "orgs": [
           "org3"
        ]
       }
   ]
   ```
   and <b>add_recursive_org_membership</b> flag is not added.<br/>
   The script will continue since the org mapping for Enterprise Admins members is not provided.
   

## Script Break Down

### Process org mapping
Populate the org mapping either via input json file or an org attribute in the ldap users/groups entity.</br>
This step creates a list of orgs to create/sync to ThoughtSpot system. Further we recursively add users and groups to
users_to_create and groups_to_create lists.</br>
If **add_recursive_org_membership** is added to the script then we recursively extend the parent's org mapping list to
its member while populating the users_to_create and groups_to_create lists.

### Validate org mapping
This step lists out the users/groups whose org mapping could not be found and reports them in the _error_log_file_.</br>
Further we validate the parent-member org assignment check which is described in the **Validations** step.

### Update ThoughtSpot
This step updates users and groups to ThoughtSpot.

#### 1. Sync Orgs
Creates orgs present in the current sync in ThoughtSpot system.<br/>
After creating, we fetch orgs list from ThoughtSpot to obtain org name to org id mapping and vice-versa.

#### 2. Sync Users
Checks if the user exists in ThoughtSpot system. If yes, update it's org mapping and sync other user properties under the
upsert flag. Else, we create the user in its corresponding orgs.</br>
_Please Note: User operations take place in All orgs context_

#### 3. Sync Groups
Creates/Sync groups in their corresponding orgs.</br>
For each org of each group, we call the sync_groups method to update thoughtSpot with the corresponding groups. Since
the groups exist at org level, same group in different orgs will be considered as different entity in ThoughtSpot.</br>
_Please Note: group operations take place in individual org's context_

#### 4. Fetch User and Groups List from ThoughtSpot
Fetch user and groups to list out which exist in the thoughtSpot system and populate org mapping in the ThoughtSpot 
system for each user and groups</br>
These mappings will be useful to identify users and groups to be purged and/or removed from orgs not present in the
current ldap sync

#### 5. Populate parent-member relationship maps
For each of the parent, we populate maps corresponding to group-user relationships and group-group relationships. This
happens for each of the parent's org. Also, to note that we only populate those user/group in the relationship map which
have an appropriate org mapping.

#### 6. Create group-user and group-group relationship in ThoughtSpot system
From the above populated maps, we create group-user and group-group relationships in ThoughtSpot 

#### 7. Delete Groups
This step is under the purge or purge_groups flag</br>
Here we delete groups which are not present in current sync or groups for whom org list is empty

#### 8. Remove Groups from Orgs
This step is under the remove_group_orgs flag</br>
Remove Group from orgs which are not there in present sync

#### 9. Delete Users
This step is under the purge or purge_users flag</br>
Deletes users which are not there in present sync or whose org list is empty

#### 10. Remove Users from Orgs
This step is under the remove_user_orgs flag</br>
Remove Users from orgs which are not there in present sync

Sample Deletion/Org Removal report:</br>
```text
===== Group Deletion Phase =====

No groups deleted

===== Group Org Removal Phase =====

cn=administrators.cn=builtin@ldap.thoughtspot.com Group Removed from ['org3'] orgs

cn=enterprise admins.cn=users@ldap.thoughtspot.com Group Removed from ['org3'] orgs

cn=read-only domain controllers.cn=users@ldap.thoughtspot.com Group Removed from ['org3'] orgs

cn=denied rodc password replication group.cn=users@ldap.thoughtspot.com Group Removed from ['org3'] orgs

===== User Deletion Phase =====

No users to delete

===== User Org Removal =====

Removed moo_100@ldap.thoughtspot.com User from orgs ['org3']
Removed tsadmin@ldap.thoughtspot.com User from orgs ['org3']
```
## Summary Reporting
**Reported Metrics:** </br>
Number of Orgs created</br>
Number of Orgs already existing in the ThoughtSpot system</br>
Number of Users created</br>
Number of Users synced</br>
Number of Groups created per org</br>
Number of Groups synced per org</br>
Number of Users deleted if the purge or purge_users flag is set</br>
Number of orgs from which each user is removed if remove_user_orgs flag is set</br>
Number of Groups deleted if the purge or purge_groups flag is set</br>
Number of orgs from which each group is removed if remove_group_orgs flag is set</br>
</br>
Ldap sync summary is reported in _sync_report_file_ </br>
Sample summary report:</br>
```text
========= Summary ========

Orgs created: 0
Orgs Already Exist: 2
Users created: 0
Users synced: 2
0 Groups created in org1 org
4 Groups synced in org1 org
0 Groups created in org2 org
4 Groups synced in org2 org
Users deleted: 0
Removed moo_100@ldap.thoughtspot.com User from 1 Orgs
Removed tsadmin@ldap.thoughtspot.com User from 1 Orgs
Groups deleted: 0
Removed cn=administrators.cn=builtin@ldap.thoughtspot.com Group from 1 Orgs
Removed cn=enterprise admins.cn=users@ldap.thoughtspot.com Group from 1 Orgs
Removed cn=read-only domain controllers.cn=users@ldap.thoughtspot.com Group from 1 Orgs
Removed cn=denied rodc password replication group.cn=users@ldap.thoughtspot.com Group from 1 Orgs

```


