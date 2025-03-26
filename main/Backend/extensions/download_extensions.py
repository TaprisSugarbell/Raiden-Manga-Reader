from main.models import extension
import requests
import os

def download_extension(extension_data):
    try:
        sourcePath = fr"{os.getcwd()}\main\Backend\extensions\{extension_data["Name"]}\\"
        source = requests.get(extension_data['source'])
        if not os.path.exists(sourcePath):
            os.mkdir(sourcePath)
        with open(sourcePath+'source.py', "wb") as script:
            script.write(source.content)
        imageBytes = requests.get(extension_data['logo'])
        staticDirectory = fr"{os.getcwd()}\main\static\\"
        logoPath = fr"extension-logos\{extension_data['Name']}{extension_data['logo'][len(extension_data['logo'])-4::]}"
        with open(staticDirectory+logoPath, "wb") as logo:
            logo.write(imageBytes.content)
        Extension = extension(name=extension_data['Name'], path=sourcePath, logo=logoPath, url=extension_data["url"].replace("com", "io"))
        Extension.save()
        return False
    except:
        return True
    