from .models import manga, extension, chapter, download, setting, category, mangaCategory
from main.Backend.extensions.download_extensions import download_extension
from django.http import HttpResponse, JsonResponse
from main.Backend.update import updateChapters, updateLibrary
from main.Backend.extensions.extension_list import ext_list
from main.Backend.extensions.search_manga import search
from main.Backend.extensions.add_manga import newManga
from main.Backend.IfOnline import connected
from django.shortcuts import render, redirect
from win10toast import ToastNotifier
import requests
import shutil
import json
import sys
import ast
import os

# from .reader import * # This line is currently not needed
# Create your views here.

def redirect_view(response):
    response = redirect('/library')
    return response

def library(response):
    library = manga.objects.all().order_by("title")
    categories = category.objects.all()
    mangaCategories = mangaCategory.objects.all()
    if response.method == "POST":
            method = response.POST["editLibrary"]
            if method == "updateLibrary":
                libraryUpdating = setting.objects.get(name="libraryUpdating")
                if libraryUpdating.state == False:
                    libraryUpdating.state = True
                    libraryUpdating.save()
                    updateLibrary()
                    libraryUpdating.state = False
                    libraryUpdating.save()
            if method == "filterCategories":
                categoryIds = response.POST.getlist("checkbox")
                filteredLibrary = []
                for categoryId in categoryIds:
                    filteredManga = mangaCategories.filter(categoryid=categoryId)
                    for filtered in filteredManga:
                        filteredLibrary.append(manga.objects.get(id=filtered.mangaid))
                library = set(filteredLibrary)
            if method == "cancelLibraryFilter":
                pass
                    
    return render(response, "main/library.html", {'library': library, 'categories': categories})

def browse(response):
    results = []
    extensions = extension.objects.all()
    if response.method == "GET":
        SearchQuery = response.GET.get('search_box', None)
        if SearchQuery is not None:
            results = search(SearchQuery)
            for k,v in results.items():
                ext = extension.objects.get(name=k)
                if len(v) > 0:
                    for k2, v2 in v.items():
                        if manga.objects.all().filter(title=k2, source=ext.id).exists():
                            mangaInLibrary = manga.objects.get(title=k2, source=ext.id)
                            results[k][k2] = [mangaInLibrary.id, mangaInLibrary.cover, True]

    if response.method == "POST":
        response.session['mangaInfo'] = response.POST['mangaInfo']
        return redirect('/comic/0/0')
    return render(response, "main/browse.html", {"results": results, "extensions": extensions})


def extensions(response):
    if response.method == "POST":
        method = response.POST.get('editExtensions', None)
        if method is not None:
            if method == 'deleteExtension':
                extensionId = response.POST['extensionId']
                print(extensionId)
                extensionToDelete = extension.objects.get(id=extensionId)
                logoPath = f"{os.getcwd()}/main/static/{extensionToDelete.logo}"
                if os.path.exists(logoPath): # checks if the image exists in the directory before deleting
                    os.remove(logoPath) # deletes the source logo
                extensionPath = f"{os.getcwd()}\main\Backend\extensions\{extensionToDelete.name}"
                if os.path.exists(extensionPath): # checks if the directory where extension should be installed exists
                    shutil.rmtree(extensionPath) #deletes extension source.py
                toast = ToastNotifier() # Notifies user of deletion
                toast.show_toast(
                    f'Extension: {extensionToDelete.name} was deleted successfully',
                    '',
                    duration=3,
                )
                linkedManga = manga.objects.all().filter(source=extensionToDelete.id)
                for linked in linkedManga:
                    chapters = chapter.objects.all().filter(comicId=linked.id)
                    for item in chapters:
                        if item.downloaded == True:
                            path = f"{os.getcwd()}\main\static\manga\{linked.id}\{item.id}"
                            if os.path.exists(path):
                                shutil.rmtree(path)
                        item.delete()
                    coverPath = f"{os.getcwd()}/main/static/{linked.cover}"
                    if os.path.exists(coverPath) == True:
                        os.remove(coverPath)
                    linked.delete()
                extensionToDelete.delete() #removes extension object from database
                return redirect("/library/")

            if method == 'downloadExtension':
                extensionData = response.POST['extension']
                downloadFailed = download_extension(ast.literal_eval(extensionData))
                if downloadFailed == True:
                    toast = ToastNotifier()
                    toast.show_toast(
                        f'Extension download failed',
                        'Check your internet connection and try again',
                        duration=3,
                    )
        else:
            extensionId = response.body
            linkedManga = manga.objects.all().filter(source=extensionId).values()
            return JsonResponse({'linkedManga':list(linkedManga)})

    allExtensions = ext_list()
    if allExtensions != -1:
        for otherExtension in allExtensions:
            if extension.objects.all().filter(name=otherExtension["Name"]).exists():
                otherExtension["downloaded"] = True
            else:
                otherExtension["downloaded"] = False
    installedExtensions = extension.objects.all()
    return render(response, "main/extensions.html", {'installed': installedExtensions, 'all': allExtensions})

def linkedManga(response):
    extensionId = response.body
    linkedManga = manga.objects.all().filter(source=extensionId).values()
    return JsonResponse({'linkedManga':list(linkedManga)})

def comic(response, id, inLibrary):
    if inLibrary == 1:
        comic = manga.objects.get(id=id)
        currentCategories = [category.objects.get(id=item.categoryid) for item in mangaCategory.objects.filter(mangaid=id)]
        allCategories = category.objects.all()
        extensionName = extension.objects.get(id=comic.source)
        if comic.updating == True:
            try:
                toast = ToastNotifier()
                toast.show_toast(
                    f'{comic.title} is being updated',
                    'Please wait a bit and try again later',
                    duration=3,
                )
                return redirect('/library/')
            except:
                return redirect('/library/') #Notification will not work if there is already an existing notification
        chapters = chapter.objects.all().filter(comicId=id).exclude(index=-1)
        ordered = chapters.order_by('index')
        if response.method == "POST":
            method = response.POST["editManga"]
            comic.editing = True
            comic.save()
            if method == "markRead":
                readChapters = response.POST.getlist("checkbox")
                for chapterId in readChapters:
                    readChapter = chapter.objects.get(id=chapterId)
                    if readChapter.read == False:
                        readChapter.read = True
                        readChapter.lastRead = 0
                        readChapter.save()
                        comic.leftToRead -= 1
                        comic.save()
            if method == "markUnread":
                unreadChapters = response.POST.getlist("checkbox")
                for chapterId in unreadChapters:
                    unreadChapter = chapter.objects.get(id=chapterId)
                    if unreadChapter.read == True:
                        unreadChapter.read = False
                        unreadChapter.lastRead = 0
                        unreadChapter.save()
                        comic.leftToRead += 1
                        comic.save()
            if method == "removeManga":
                for item in chapters:
                    if item.downloaded == True:
                        path = f"{os.getcwd()}\main\static\manga\{comic.id}\{item.id}"
                        if os.path.exists(path):
                            shutil.rmtree(path)
                    item.delete()
                os.remove(f"{os.getcwd()}/main/static/{comic.cover}")
                mangaCategory.objects.filter(mangaid=comic.id).delete()
                comic.delete()
                return redirect("/library/")
            if method == "downloadSelected":
                if connected() == True:
                    ext = extension.objects.get(id=comic.source)
                    sys.path.insert(0, ext.path)
                    import source
                    selectedChapters = response.POST.getlist("checkbox")
                    for chapterId in selectedChapters:
                        selectedChapter  = chapter.objects.get(id=chapterId)
                        if selectedChapter.downloaded == False:
                            download.objects.create(name=selectedChapter.name, chapterid=selectedChapter.id, mangaName=comic.title)
                        if selectedChapter.downloaded == True:
                            selectedChapters.remove(chapterId)
                    toast = ToastNotifier()
                    toast.show_toast(
                        f'{len(selectedChapters)} Chapter(s) Are Being Downloaded',
                        'Check progress in the downloads page\nDo not close the program',
                        duration=3,
                    )
                    failedDownloads = 0
                    for chapterId in selectedChapters:
                        if selectedChapter.downloaded == False:
                            selectedChapter = chapter.objects.get(id=chapterId)
                            chapterDownloading = download.objects.get(chapterid=selectedChapter.id)
                            images = source.GetImageLinksNoProxy(selectedChapter.url)
                            if len(images) == 0:
                                failedDownloads += 1
                                chapterDownloading.delete()
                            else:
                                chapterDownloading.totalPages = len(images)
                                chapterDownloading.save()
                                downloadFailed = source.DownloadChapter(images, comic.id, selectedChapter.id, chapterDownloading.id)
                                if downloadFailed == True:
                                    failedDownloads += 1
                                    path = f"{os.getcwd()}\main\static\manga\{id}\{chapterId}"
                                    if os.path.exists(path):
                                        shutil.rmtree(path)
                                    selectedChapter.downloaded = False
                                    selectedChapter.save()
                    if failedDownloads > 0:
                        toast = ToastNotifier()
                        toast.show_toast(
                            f'Download Failed for {failedDownloads} Chapter(s)',
                            'Check your internet connection or try again',
                            duration=3,
                        )
                else:
                    toast = ToastNotifier()
                    toast.show_toast(
                        f'Download(s) Failed',
                        'Check your internet connection or try again',
                        duration=3,
                    )              
            if method == "deleteDownloaded":
                selectedChapters = response.POST.getlist("checkbox")
                for chapterId in selectedChapters:
                    selectedChapter  = chapter.objects.get(id=chapterId)
                    if selectedChapter.downloaded == True:
                        path = f"{os.getcwd()}\main\static\manga\{comic.id}\{chapterId}"
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        selectedChapter.downloaded = False
                        selectedChapter.save()
            comic.editing = False
            comic.save()

            if method == "showDownloaded":
                chapters = chapter.objects.all().filter(comicId=id, downloaded=True)
            if method == "showRead":
                chapters = chapter.objects.all().filter(comicId=id, read=True)
            if method == "showUnread":
                chapters = chapter.objects.all().filter(comicId=id, read=False)
            if method == "cancelFilter":
                pass
            if method == "updateChapters":
                if comic.updating == False:
                    toast = ToastNotifier()
                    toast.show_toast(
                        'Update is taking place',
                        "Closing the app prematurely will cause manga to be deleted",
                        duration=4,
                    )
                    updated = updateChapters(id)
                    if updated == -1:
                        toast = ToastNotifier()
                        toast.show_toast(
                            'Update Failed',
                            f"Make sure you are connected to the internet or try again",
                            duration=4,
                        )
                    if len(updated) == 0:
                        toast = ToastNotifier()
                        toast.show_toast(
                            f'Update Completed',
                            f"No new chapters are available",
                            duration=4,
                        )
                    if len(updated) > 0:
                        toast = ToastNotifier()
                        toast.show_toast(
                            f'{comic.title}',
                            f"{','.join(updated)}",
                            duration=4,
                        )
                        leftToRead = len(chapter.objects.filter(comicId=id).exclude(read=True))
                        numChapters = len(chapter.objects.filter(comicId=id))
                        comic.leftToRead = leftToRead
                        comic.numChapters = numChapters
                        comic.save()
            if method == "editCategories":
                newCategories = response.POST.getlist("checkbox")
                for item in currentCategories:
                    if item.id not in newCategories:
                        mangaCategoryToDelete = mangaCategory.objects.get(categoryid=item.id, mangaid=id)
                        if mangaCategoryToDelete.categoryid != category.objects.get(name="All").id:
                            mangaCategoryToDelete.delete()
                for categoryId in newCategories:
                    if not mangaCategory.objects.all().filter(categoryid=categoryId, mangaid=id).exists():
                        mangaCategory.objects.create(categoryid=categoryId, mangaid=id)
                currentCategories = [category.objects.get(id=item.categoryid) for item in mangaCategory.objects.filter(mangaid=id)]

        nextChapter = -1
        if len(ordered) > 0:
            nextChapter = ordered[0].index
            for item in ordered:
                nextChapter = item.index
                if item.read == False:
                    break
            if nextChapter == comic.numChapters:
                if chapter.objects.get(index=nextChapter, comicId=comic.id).read == True:
                    nextChapter = -1
    elif inLibrary == 0:
        mangaInfo = response.session.get('mangaInfo').split(',')
        ext = extension.objects.get(name=mangaInfo[0])
        if response.method == "POST":
            # newItem = manga.objects.create(name="")
            mangaId = newManga(ext, response.session.get("chapters"), response.session.get("metaData"))
            if mangaId == -1:
                toast = ToastNotifier()
                toast.show_toast(
                    f'Failed to add manga to library',
                    'Check your internet connection or try again',
                    duration=3,
                )
                return redirect('/library/')
            return redirect(f'/comic/1/{mangaId}')
        sys.path.insert(0, ext.path)
        import source
        comic = source.GetMetadata(mangaInfo[1])
        
        chapters = source.GetChapters(mangaInfo[1])
        if (chapters == -1) or (comic == -1):
            toast = ToastNotifier()
            toast.show_toast(
                f'Failed to view Manga',
                'Check your internet connection or try again',
                duration=3,
            )
            return redirect('/library/')
        # print(mangaInfo[1])
        # print(chapters)
        response.session['chapters'] = chapters
        response.session['metaData'] = comic
        return render(response, "main/browse_comic.html", {"comic":comic, "chapters":chapters})        

    return render(response, "main/comic.html", {"comic":comic, "chapters":chapters, "nextChapter": nextChapter, "allCategories": allCategories, "currentCategories":currentCategories, "extensionName":extensionName})

def read(response, inLibrary, comicId, chapterIndex):
    comic = manga.objects.get(id=comicId)
    if comic.updating == True:
        toast = ToastNotifier()
        toast.show_toast(
            f'{comic.title} is being updated',
            'Please wait a bit and try again later',
            duration=3,
        )
        return redirect('/library/')
    currentChapter = chapter.objects.get(comicId=comic.id, index=chapterIndex)
    if response.method == "POST":
        data = json.loads(response.body)
        if data["value"] == "Completed":
            currentChapter.lastRead = data['lastRead']
            if currentChapter.read == False:
                currentChapter.read = True
                currentChapter.save()
                comic.leftToRead -= 1
                comic.save()
        if data["value"] == "orientation":
            comic.orientation = data['orientation']
            comic.save()
        if data["value"] == "lastRead":
            currentChapter.lastRead = data['lastRead']
            currentChapter.save()

    else:
        if currentChapter.downloaded == True:
            path = f"{os.getcwd()}\main\static\manga\{comicId}\{currentChapter.id}"
            if os.path.exists(path) == False:
                try:
                    toast = ToastNotifier()
                    toast.show_toast(
                        'Downloaded Chapters are missing from directory',
                        f"Redownload chapter if you wish to read offline",
                        duration=4,
                    )
                    currentChapter.downloaded = False
                    currentChapter.save()
                    return redirect(f"/comic/1/{comicId}/")
                except:
                    return redirect(f"/comic/1/{comicId}/") #Toast notification will break if there is an existing notification that has been sent
            unsortedImages = os.listdir(path)
            if len(unsortedImages) == 0:
                try:
                    toast = ToastNotifier()
                    toast.show_toast(
                        'Downloaded Chapters are missing from directory',
                        f"Redownload chapter if you wish to read offline",
                        duration=4,
                    )
                    currentChapter.downloaded = False
                    currentChapter.save()
                    return redirect(f"/comic/1/{comicId}")
                except:
                    return redirect(f"/comic/1/{comicId}")
            images = []
            pagesMissing = False
            for i in range(1, len(unsortedImages)+1):
                try:
                    if "1.png" in unsortedImages:
                            images.append(f"manga/{comicId}/{currentChapter.id}/" + unsortedImages[unsortedImages.index(f"{str(i)}.png")])
                    if "1.jpg" in unsortedImages:
                            images.append(f"manga/{comicId}/{currentChapter.id}/" + unsortedImages[unsortedImages.index(f"{str(i)}.jpg")])
                    else:
                        pagesMissing = True
                except:
                    pagesMissing = True
            if pagesMissing == True:
                toast = ToastNotifier()
                toast.show_toast(
                    'There are some issues with this chapter ⚠',
                    f"Pages may be missing, you may want to redownload",
                    duration=4,
                )
        else:
            if connected() == True:
                ext = extension.objects.get(id=comic.source)
                sys.path.insert(0, ext.path)
                import source
                images = source.GetImageLinks(currentChapter.url)
                if len(images) == 0:
                    toast = ToastNotifier()
                    toast.show_toast(
                        'Failed to retrieve chapter images',
                        f"Check Your internet connection",
                        duration=4,
                    )
                    return redirect(f"/comic/1/{comicId}")
            else:
                try:
                    toast = ToastNotifier()
                    toast.show_toast(
                        'Failed to retrieve chapter images',
                        f"Check Your internet connection",
                        duration=4,
                    )
                    return redirect(f"/comic/1/{comicId}")
                except:
                    return redirect(f"/comic/1/{comicId}") #Notification will fail if there is an existing notification

        return render(response, "main/read.html", {"comic": comic, "chapter": currentChapter, "images": images})

def downloads(response):
    currentDownloads = download.objects.all().order_by('-id')
    if response.method == "POST":
        data = json.loads(response.body)
        if data["value"] == "cancelDownload":
            downloadId = data["downloadId"]
            if download.objects.all().filter(id=downloadId).exists():
                download.objects.get(id=downloadId).delete()
    return render(response, "main/downloads.html", {"downloads": currentDownloads})

def downloadProgress(response):
    currentDownloads = download.objects.all().order_by('-id').values()
    return JsonResponse({"downloads":list(currentDownloads)})

def bypass(response, extensionId, imageUrl):
    sourceUrl = extension.objects.get(id=extensionId).url
    headers = {
        'Referer': sourceUrl,
    }
    imageData = (requests.get(imageUrl, headers=headers)).content
    return HttpResponse(imageData, content_type="image/png")

def settings(response):
    automaticUpdates = setting.objects.get(name="automaticUpdates")
    if response.method == "POST":
        method = response.POST["editSetting"]
        if method == "newCategory":
            categoryName = response.POST["categoryName"]
            if category.objects.all().filter(name=categoryName).exists():
                toast = ToastNotifier()
                toast.show_toast(
                    f'Category already exists!',
                    'Category names must be unique',
                duration=3,
                )
            else:
                category.objects.create(name=categoryName)
        if method == "deleteCategory":
            categoryName = response.POST["categoryName"]
            categoryToDelete = category.objects.get(name=categoryName)
            mangaCategory.objects.all().filter(categoryid=categoryToDelete.id).delete()
            categoryToDelete.delete()
        if method == "editUpdate":
            automaticUpdatesAllowed = response.POST["automaticUpdates"]
            if automaticUpdatesAllowed == "True":
                updateFrequency = response.POST["updateFrequency"]
                automaticUpdates.state = True
                automaticUpdates.value = int(updateFrequency)
                automaticUpdates.save()
            else:
                automaticUpdates.state = False
                automaticUpdates.save()
            toast = ToastNotifier()
            toast.show_toast(
                f'Update Settings were changed',
                'Please restart app for changes to take place',
            duration=3,
            )
    categories = category.objects.all().exclude(name="All")
    return render(response, "main/settings.html", {"categories": categories, "automaticUpdates": automaticUpdates})