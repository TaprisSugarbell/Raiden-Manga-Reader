from main.models import manga, chapter, mangaCategory, category
from main.Backend.IfOnline import connected
from pathlib import Path
import requests
import hashlib
import os

def newManga(ext, chapters, metaData):
    # sys.path.insert(0, ext.path)
    # import source
    numChapters = len(chapters)
    if connected():
        try:
            request = requests.get(metaData["cover"])
            fileName = os.path.join("covers", hashlib.md5(request.content).hexdigest() + metaData["cover"][ len(metaData["cover"]) -4::])
            path = Path.cwd() / "main" / "static"
            if not os.path.exists(path / fileName): #there would be a collision if the same image is already saved, only save if it doesn't exist
                with open(path / fileName, "wb") as cover:
                    cover.write(request.content)
        except:
            return -1
    else:
        return -1
    newManga = manga.objects.create(title=metaData["name"], url=metaData["url"], cover=fileName, description=metaData["description"], source=ext.id, author=metaData["author"], orientation="vertical", numChapters=numChapters, leftToRead=numChapters)
    all = category.objects.get(name="All")
    mangaCategory.objects.create(categoryid=all.id, mangaid=newManga.id)
    reversed = chapters[::-1]
    for item in chapters:
        chapter.objects.create(name=item["name"], url=item["url"], comicId=newManga.id, index=reversed.index(item)+1)
    return newManga.id