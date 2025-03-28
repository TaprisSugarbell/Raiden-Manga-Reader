from main.models import manga, extension, chapter, setting
from main.Backend.IfOnline import connected
import time
import sys
import os

PLATFORM = os.name

if PLATFORM == "nt":
    from win10toast import ToastNotifier

def updateLibrary():
    library = manga.objects.all()
    if len(library) > 0:
        if connected():
            if PLATFORM == "nt":
                toast = ToastNotifier()
                toast.show_toast(
                    'Update is taking place',
                    "Closing the app prematurely will cause manga to be deleted",
                    duration=4,
                )
            updates = []
            for comic in library:
                if manga.objects.all().filter(id=comic.id).exists():
                    if not comic.updating:
                        print(comic.updating)
                        update = updateChapters(comic.id)
                        if len(update) > 0:
                            updates.append(comic.title)
                            leftToRead = len(chapter.objects.filter(comicId=comic.id).exclude(read=True))
                            numChapters = len(chapter.objects.filter(comicId=id))
                            comic.leftToRead = leftToRead
                            comic.numChapters = numChapters
                            comic.save()
            if len(updates) > 0:
                if PLATFORM == "nt":
                    toast = ToastNotifier()
                    toast.show_toast(
                        f'New Chapters',
                        f"{', '.join(updates)}",
                        duration=4,
                    )
            if len(updates) == 0:
                if PLATFORM == "nt":
                    print("Update Completed")
                    print(f"No new chapters are available")
        else:
            if PLATFORM == "nt":
                toast = ToastNotifier()
                toast.show_toast(
                    'Automatic Update Failed',
                    "Make sure you are connected to the internet",
                    duration=4,
                )

def updateChapters(comicId):
    if connected():
        comic = manga.objects.get(id=comicId)
        if comic.editing:
            if PLATFORM == "nt":
                toast = ToastNotifier()
                toast.show_toast(
                    f'Update for {comic.title} skipped',
                    "Manga is currently being edited",
                    duration=4,
                )
            return []
        comic.updating = True
        comic.save()
        chapters = chapter.objects.all().filter(comicId=comicId)
        ext = extension.objects.get(id=comic.source)
        sys.path.insert(0, ext.path)
        import source
        newChapters = source.GetChapters(comic.url) # fetches the data for chapters from source
        reversed = newChapters[::-1]
        for currentChapter in chapters:
            currentChapter.index = -1 # changes the index of all the current chapters to -1
            currentChapter.save()
        for newChapter in newChapters:
            chapter.objects.create(name=newChapter["name"], url=newChapter["url"], comicId=comicId, index=reversed.index(newChapter)+1)
        ## TODO: Need to go through the database, link chapters by name and transfer properties such as downloaded and so on
        chapters = chapter.objects.all().filter(comicId=comicId).exclude(index=-1)
        updated = []
        for newChapter in chapters:
            filtered = chapter.objects.filter(comicId=comicId, name=newChapter.name).order_by('index')
            if len(filtered) > 1:
                read, lastRead, downloaded = filtered[0].read, filtered[0].lastRead, filtered[0].downloaded
                if downloaded:
                    path = fr"{os.getcwd()}\main\static\manga\{comicId}\{filtered[0].id}"
                    newPath = fr"{os.getcwd()}\main\static\manga\{comicId}\{filtered[1].id}"
                    os.rename(path, newPath)
                filtered[1].read = read 
                filtered[1].lastRead = lastRead
                filtered[1].downloaded =  downloaded
                filtered[1].save()
                filtered[0].delete()
            else:
                updated.append(filtered[0].name)
        comic.updating = False
        comic.save()
        return updated
    else:
        if PLATFORM == "nt":
            toast = ToastNotifier()
            toast.show_toast(
                'Update Failed',
                "Make sure you are connected to the internet or try again",
                duration=4,
            )
        return -1

def autoUpdate(frequency):
    libraryUpdating = setting.objects.get(name="libraryUpdating")
    if libraryUpdating.state == False:
        libraryUpdating.state = True
        libraryUpdating.save()
        updateLibrary()
        libraryUpdating.state = False
        libraryUpdating.save()
    time.sleep(frequency)
    autoUpdate(frequency)

def updateOnStart():
    libraryUpdating = setting.objects.get(name="libraryUpdating")
    if libraryUpdating.state == False:
        libraryUpdating.state = True
        libraryUpdating.save()
        updateLibrary()
        libraryUpdating.state = False
        libraryUpdating.save()

