#!/user/bin/python3
import sys
import requests
import json

def usage():
    print("Usage: ./transferOwnership.py3 url:http[s]://cluster_ip:port from_username to_username [\"json array of tag_names\"] type")

def validateArgs():
    print("Arguments passed are", sys.argv)
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        usage()
        exit(1)

def getObjectMetadataForTag(cluster_ip, tagName, cookie, types="ALL"):
    url="/callosum/v1/tspublic/v1/metadata/listobjectheaders"
    objectsIDName = {}
    headers = {
        "X-Requested-By":"ThoughtSpot",
        "Accept":"application/json",
        "Content-Type":"application/json"
    }
    cookies = {
        "JSESSIONID":cookie
    }
    for type in types.split(","):
        params = {
            "type":type,
            "tagname":tagName
        }
        response = requests.get(url = cluster_ip+url, params = params, cookies = cookies, headers = headers)
        if response.status_code != 200:
            print("Error while fetching objects")
            print("Status code is", response.status_code)
            print("Response content is", response.content)
            exit(1)
        for item in response.json():
            id = item["id"]
            author = item["author"]
            objectsIDName[id] = author
    return objectsIDName


def login(cluster, username="username", password="password"):
    url = "/callosum/v1/tspublic/v1/session/login"
    print("logging in", cluster+url, "as", username)
    header = {
        "X-Requested-By":"ThoughtSpot",
        "Accept":"application/json",
        "Content-Type":"application/x-www-form-urlencoded"
    }
    data = {
        "username": username,
        "password": password,
        "rememberme":"true"
    }
    response = requests.post(url=cluster+url, data = data, headers = header, verify = False)
    if response.status_code != 204:
        print("Error while logging in")
        print(response.status_code)
        print(response.content)
        exit(1)
    if "Set-Cookie" in response.headers:
        cookies = response.headers["Set-Cookie"]
    for cookie in cookies.split(";"):
        if cookie.startswith("JSESSIONID"):
            TScookie = cookie.split("=")[1]
            print("Cookie is",TScookie)
            return TScookie

def printOjbectIDAuthor(objectsIDName, isDiff, newObjectsIDName={}):
    if isDiff == True:
        print("ID                                                                old_author                                    new_author")
        for id in objectsIDName.keys():
            print(id,"              ",objectsIDName[id],"               ",newObjectsIDName[id])
    else:
        print("ID                                                                Author")
        for IDName in objectsIDName.keys():
            print(IDName,"              ",objectsIDName.get(IDName))

def updateAuthor(cluster_ip, from_user, to_user, objectsIDName, cookie):
    url = "/callosum/v1/tspublic/v1/user/transfer/ownership"
    headers = {
        "X-Requested-By":"ThoughtSpot",
        "Accept":"application/json",
        "Content-Type":"application/json"
    }
    cookies = {
        "JSESSIONID":cookie
    }
    data = {
        "fromUserName":from_user,
        "toUserName":to_user,
        "objectsID":json.dumps(list(objectsIDName.keys()))
    }
    response = requests.post(url=cluster_ip+url,cookies=cookies,params=data,headers=headers)
    if response.status_code != 204:
        print("Error while changin ownership")
        print("Status code:",response.status_code)
        print("Trace ID",response.headers["X-Callosum-Trace-Id"])
        print("Response content",response.content)
        exit(1)
    
if __name__ == "__main__":
    validateArgs()
    cookie = login(sys.argv[1])
    objectsIDName = getObjectMetadataForTag(sys.argv[1], sys.argv[4], cookie, sys.argv[5])
    printOjbectIDAuthor(objectsIDName,False)
    updateAuthor(sys.argv[1], sys.argv[2], sys.argv[3], objectsIDName, cookie)
    newObjectsIDName = getObjectMetadataForTag(sys.argv[1], sys.argv[4], cookie, sys.argv[5])
    printOjbectIDAuthor(objectsIDName,True,newObjectsIDName)