Only as an example script for testing not ready for production.

This script will:
1. Login to the cluster with tspublic login API, username and password are hardcoded in the script
   need to change them before running the script.
2. Fetch all the objects with tag tag_name.
3. Update the ownership of objects from user1 to user2 only for the objects which are present
in the fetched set.
   
e.g.
TAG         OBJECT_ID       OWNER
tag1        OBJECT_ID1      USER1
tag1        OBJECT_ID2      USER2
tag2        OBJECT_ID3      USER1

If I run the script to change the ownership of objects from user1 to user2. Then first it will fetch
the OBJECTS with tag1:

TAG         OBJECT_ID       OWNER
tag1        OBJECT_ID1      USER1
tag1        OBJECT_ID2      USER2

Then for each object owned by user1, if the object_id is present in the fetched object ids i.e.
['OBJECT_ID1','OBJECT_ID2'] change the ownership of that object. So final result will be:

TAG         OBJECT_ID       OWNER
tag1        OJBJECT_ID1     USER2  <-- only this will be changed.
tag1        OBJECT_ID2      USER2
tag2        OBJECT_ID3      USER1

Usage: 

updateOwnership.py3 http[s]://IP:PORT from_user_name to_user_name "[\"tag1\",\"tag2\"]" LOGICAL_TABLE,PINBOARD_ANSWER_BOOK,QUESTION_ANSWER_BOOK

1. first argument should be protocol://ip:port
2. Change ownership of objects from this user.
3. Change ownership of objects to this user.
4. Json array of tags.
5. Comma separated Metadata Types.

Also in the login function username and password are hardcoded. Need to update those before
running the script.

