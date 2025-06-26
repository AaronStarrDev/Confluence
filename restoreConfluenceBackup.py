import requests
import json

#https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#about

BASE_URL = "https://aaronstarrdev.atlassian.net/wiki/api/v2"
BASE_URL_V1 = "https://aaronstarrdev.atlassian.net/wiki/rest/api"
USERNAME = "aaronstarrdev@gmail.com"
#API token txt file should just be the token string
with open("confluenceAPITokenAllAccess.txt", "r") as file:
    API_TOKEN = file.read().strip()

# auth tuple
AUTH = (USERNAME, API_TOKEN)


def restore_page(restoreFilePath, restoreFileName):
    restoreFileContentPath = restoreFilePath+"\\"+restoreFileName+".json"
    restoreFileRestrictionsPath = restoreFilePath+"\\"+restoreFileName+"-confrestrict.json"
    with open(restoreFileContentPath, 'r') as file:
            importedData = json.load(file)
    url = f"{BASE_URL}/pages"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "type": "page",
        "status": "current",
        "title": importedData["title"],
        "spaceId": importedData['spaceId'],
        "body": {
            "representation": "storage",
            "value": importedData['body']['storage']['value']
        }
    }

    if importedData["parentId"]:
        payload["parentId"] = importedData["parentId"]

    response = requests.request("POST", url, headers=headers, auth=AUTH, data=json.dumps(payload))

    if response.status_code == 200 or response.status_code == 201:
        page_id = response.json().get("id")
        restore_page_restrictions(page_id, restoreFileRestrictionsPath)
    else:
        print(f"Failed to restore content page '{importedData["title"]}': {response.status_code} - {response.text}")
        return None
    

def restore_page_restrictions(page_id, restriction_file):
    with open(restriction_file, "r", encoding="utf-8") as f:
        restrictions = json.load(f)

    url = f"{BASE_URL_V1}/content/{page_id}/restriction"
    headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
    }

    response = requests.put(
        url,
        headers=headers,
        auth=AUTH,
        data=json.dumps(restrictions)
    )

    if response.status_code in (200, 204):
        print(f"Restored restrictions to page {page_id}")
    else:
        print(f"Failed to restore restriction: {response.status_code} - {response.text}")



def main():
    restore_url = r"C:\Temp\Confluence_Backup\Visual Studios"
    restore_file_name = "Visual Studios - Setup"
    restore_page(restore_url,restore_file_name)

if __name__ == "__main__":
    main()