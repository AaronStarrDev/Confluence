import os
import requests
import json
import urllib.parse

#https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#about

# Do not currently save every type of attachment. (.docx doesn't work, where .yml does)

# This process will create 3 files for each page, and 1 folder for each folder.
# The 3 files are:
# 1: styled_view | HTML |  this makes it easier to examine the page locally and see the data in a well-formatted way. Cannot be restored from
# 2: storage | JSON | this view is accepted by the api to create a page. Can be restored from. (Found inside the .json file at body > storage)
# 3: Restrictions | JSON | This file is the restrictions (or permissions) set on a page and is used to make the same permissions on a restored page.
# The 1 folder is named after the title of the folder in Confluence, due to folder naming restrictions, some special charcters are replaced

BASE_URL = "https://aaronstarrdev.atlassian.net/wiki/api/v2"
BASE_URL_V1 = "https://aaronstarrdev.atlassian.net/wiki/rest/api"
USERNAME = "aaronstarrdev@gmail.com"
#API token txt file should just be the token string
#current permissions for read:hierarch... for the v2 api get descendants call is not available, must use full access to my knowledge
with open("confluenceAPITokenAllAccess.txt", "r") as file:
    API_TOKEN = file.read().strip()
# Since these are created as folders, directories don't like special characters. Replaced . with _
top_level_folders = {
    '4325377': 'Visual Studios',
    '4390926': 'AI',
    '4587522': 'Google',
    '7766017': 'AWS',
    '7798785': 'Azure',
    '7798787': 'Windows',
    '7766019': 'PowerShell'
}

# auth tuple
AUTH = (USERNAME, API_TOKEN)



def safe_filename(title: str) -> str:
    """
    Returns a filesystem-safe version of the title.
    '[c... for c in title]' - loop through each character in the string
    '...if c.isalnum()...' - don't touch alphanumeric characters (a-z, A-Z, 0-9)
    '...or c in " _-"' - allow spaces, underscores, and hyphens
    '...else "_"...' - replace all other characters (/?*:") with underscores
    '"".join([...])' - join all characters into a string
    '.string()' - remove leading and trailing whitespace
    """
    return "".join([c if c.isalnum() or c in " _-" else "_" for c in title]).strip()



def save_page_content(page_data: dict, folder: str, body_type: str):
    """
    Save the page content (HTML in Storage Format) to an HTML file in the specified folder.
    """
    title = page_data.get("title", "untitled")
    safe_title = safe_filename(title)
    file_name = f"{safe_title}.html"
    file_path = os.path.join(folder, file_name)

    # Extract the HTML content from the Confluence storage format.
    content = page_data.get("body", {}).get(body_type, {}).get("value", "")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    #print(f"Saved page: {file_path}")



def save_page_restrictions(page_data: dict, folder: str):
    """
    Save the page content (HTML in Storage Format) to an HTML file in the specified folder.
    """
    title = page_data.get("title", "untitled")
    safe_title = safe_filename(title)
    file_name = f"{safe_title}-confrestrict.json"
    file_path = os.path.join(folder, file_name)
    page_id = page_data['id']

    # v2 api doesn't have this capability currently, below is probably what it will be in v2 (currently returns: "Under construction")
    # {BASE_URL}/pages/{page_id}/restrictions
    url = f"{BASE_URL_V1}/content/{page_id}/restriction" 

    headers = {
    "Accept": "application/json"
    }

    response = requests.request(
    "GET",
    url,
    headers=headers,
    auth=AUTH
    )

    if response.status_code != 200:
        print(f"Error fetching restrictions for page {page_id}: {response.text}")
        return {}
    
    restrictions = response.json()
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(restrictions, f, indent=2)



def save_page_metadata(page_data: dict, folder: str):
    title = page_data.get("title", "untitled")
    safe_title = safe_filename(title)
    file_path = os.path.join(folder, f"{safe_title}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(page_data, f, indent=2)



def fetch_page_details(page_id: str, body_type: str) -> dict:
    """
    Retrieve full details for a page, including its content.
    """
    # Expand body.storage to retrieve exportable HTML.
    url = f"{BASE_URL}/pages/{page_id}"
    params = {
            "body-format": body_type
    }
    #params = {"expand": "body.storage,version"}
    response = requests.get(url, params=params, auth=AUTH)
    if response.status_code != 200:
        print(f"Error fetching details for page {page_id}: {response.text}")
        return {}
    return response.json()



def process_page(page: dict, folder: str):
    """
    Process each child, storing them in a subfolder named after the page.
    """
    # body_type changes what the output html file looks like, acceptable types:
    # storage, atlas_doc_format, view, export_view, anonymous_export_view, styled_view, editor
    body_types = ["styled_view","storage"]
    for body_type in body_types:
        page_details = fetch_page_details(page["id"], body_type)
        if page_details and body_type == "storage": #restorable format inside .json file
            #update_page(page["id"], page_details) can be used for sorting pages, very inefficient though.
            save_page_metadata(page_details, folder)
        elif page_details: # any other body type desired as .html
            save_page_restrictions(page_details, folder)
            save_page_content(page_details, folder, body_type)
        else:
            print(f"Skipping page {page['id']} due to fetch error.")



def update_page(page_id: str, page_details: dict):
    """
    Update page, causing it to sort them correctly. (Move the page)
    To sort them, they need to be moved to a different folder, then moved back. Once moved back they will be at the bottom of the folder.
    Position parameter/payload appears not do anything

    Very bad way to sort pages, feature request for atlassian to implement a better way is opened already on their forums
    """

    if(page_id == '4325379'):
        endpoint = f"{BASE_URL}/pages/{page_id}"
        testParentId = 4325377

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = json.dumps( {
            "id": page_id,
            "status": "current",
            "title": page_details['title'],
            "parentId": testParentId, #page_details['parentId'],
            #"position": 0, doesnt seem to do anything
            "body": {
                "representation": "storage",
                "value": page_details['body']['storage']['value']
            },
            "version": {
                "number": page_details['version']['number'] + 1,
                "message": ""
            }
        } )

        response = requests.request(
            "PUT",
            endpoint,
            data=payload,
            headers=headers,
            auth=AUTH
        )

        print("hola")



def save_folder_info(folder_id: str, folder_root: str):
    """
    Recursively retrieve all immediate descendants of a folder and process them.
    - If descendant is a folder, recurse into it.
    - If descendant is a page, call process_page.

    This recursion is depth-first
    """

    #descendants = []
    cursor = None
    limit = 250 # max limit is 250
    depth = 1  # max depth is 5
    endpoint = f"{BASE_URL}/folders/{folder_id}/descendants"
    headers = {"Accept": "application/json"}

    while True:
        # specify parameters (query parameters)
        # query parameters will be added to the end of the url, like .../descendants?depth=5&limit=250
        params = {
            "depth": depth,
            "limit": limit
        }
        if cursor:
            params["cursor"] = cursor

        # call the api and attempt to get the information needed
        response = requests.request(
            "GET",
            endpoint,
            headers=headers,
            params=params,
            auth=AUTH
        )

        if response.status_code != 200:
            print(f"Failed for folder {folder_id}: {response.status_code} - {response.text}")
            break

        data = response.json()
        #descendants.extend(data.get("results", []))

        results = data.get("results", [])

        # sort based on the title. Results is a list of dictionaries. Sorted also seems decently slow, maybe a better sort would be better?
        # python's sorted() sorts lexicographically, meaning by ASCII code. For example, AWS comes before Act, since 'W' is 87 and 'c' is 99 in ASCII
        #sorted_results = sorted(results, key=lambda x: x['title'])
        #for item in sorted_results:

        for item in results:    
            item_type = item.get("type")
            title = item.get("title", "Untitled")
            safe_title = safe_filename(title)

            if item_type == "folder":
                # Create a folder for the subfolder
                subfolder_path = os.path.join(folder_root, safe_title)
                os.makedirs(subfolder_path, exist_ok=True)
                print(f"Created folder: {subfolder_path}")

                # Recurse into the subfolder
                save_folder_info(item["id"], subfolder_path)

            elif item_type == "page":
                #print(f"Processing page: {title}")
                process_page(item, folder_root)

        # API will return a cursor if there are more pages beyond the limit. Look for the cursor to continue pagination
        next_link = data.get("_links", {}).get("next")
        if not next_link:
            break  # Done paginating

        # take the next_linl (url) and break it into the base_url string, and query string
        parsed = urllib.parse.urlparse(next_link)
        # break the query string into the separate query parameters
        query_params = urllib.parse.parse_qs(parsed.query)
        # check for the cursor query parameter
        cursor = query_params.get("cursor", [None])[0]



def main():
    for folder_id, folder_name in top_level_folders.items():
        backup_root = fr"C:\Temp\Confluence_Backup\{folder_name}"
        os.makedirs(backup_root, exist_ok=True)

        print(f"Fetching information for {folder_name}")
        save_folder_info(folder_id, backup_root)
        print(f"{folder_name} Information saved.")

if __name__ == "__main__":
    main()