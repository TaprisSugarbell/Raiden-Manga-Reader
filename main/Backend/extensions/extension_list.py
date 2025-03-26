import requests
import json

# index = "https://raw.githubusercontent.com/TaprisSugarbell/Raidenyomi-extensions/master/extension-list.json"
index = "https://raw.githubusercontent.com/TaprisSugarbell/Raidenyomi-extensions/refs/heads/master/extension-list.json"

def ext_list():
        try:
                request = requests.get(index)
                all_extensions = json.loads(request.text)
                return all_extensions
        except Exception as e:
                print(e)
                return -1
        
    
