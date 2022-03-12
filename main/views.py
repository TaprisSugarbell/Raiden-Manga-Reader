from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
from .models import manga, extension, chapter
from main.Backend.extensions.extension_list import ext_list
from main.Backend.extensions.download_extensions import download_extension
from main.Backend.extensions.search_manga import search
import requests
import sys
import ast
# from .reader import * # This line is currently not needed
# Create your views here.


def redirect_view(response):
    response = redirect('/library')
    return response

def library(response):
    library = manga.objects.all
    return render(response, "main/library.html", {'library': library})

def browse(response):
    results = []
    extensions = extension.objects.all()
    if response.method == "GET":
        SearchQuery = response.GET.get('search_box', None)
        if SearchQuery is not None:
            results = search(SearchQuery)
            print(results)
    if response.method == "POST":
        # print(response.POST['mangaInfo'])
        response.session['mangaInfo'] = response.POST['mangaInfo']
        return redirect('/comic/0/0')
    return render(response, "main/browse.html", {"results": results, "extensions": extensions})


def extensions(response):
    if response.method == "POST":
        extension_data = response.POST['extension']
        download_extension(ast.literal_eval(extension_data))
    all_extensions = ext_list()
    installed_extensions = extension.objects.all()
    return render(response, "main/extensions.html", {'installed': installed_extensions, 'all': all_extensions})

def novel(response, id):
    # content = epub2text('E:\Abdullah\Code\Python\Computer Science  NEA\master\Shogan-Manga-Reader-main\main\book2.epub')
    novel = manga.objects.get(id=id)
    return render(response, "main/novel.html", {"novel":novel})

def comic(response, id, inLibrary):
    if inLibrary == 1:
        if response.method == "POST":
            data = json.loads(response.body)
            if data["value"] == "read":
                readChapter = chapter.objects.get(id=data["chapterid"])
                readChapter.read = True
                readChapter.lastRead = 0
                readChapter.save()
            if data["value"] == "unread":
                unreadChapter = chapter.objects.get(id=data["chapterid"])
                unreadChapter.read = False
                unreadChapter.lastRead = 0
                unreadChapter.save()

        comic = manga.objects.get(id=id)
        chapters = chapter.objects.all().filter(comicId=id)

    elif inLibrary == 0:
        mangaInfo = response.session.get('mangaInfo').split(',')
        ext = extension.objects.get(name=mangaInfo[0])
        sys.path.insert(0, ext.path)
        import source
        comic = source.GetMetadata(mangaInfo[1])
        if response.method == "POST":
            # newItem = manga.objects.create(name="")
            print(comic)
        
        chapters = source.GetChapters(mangaInfo[1])
        response.session['Chapters'] = chapters
        return render(response, "main/browse_comic.html", {"comic":comic, "chapters":chapters})        

    return render(response, "main/comic.html", {"comic":comic, "chapters":chapters})

def read(response, inLibrary, comicId, chapterIndex):
    currentChapter = chapter.objects.get(index=chapterIndex)
    comic = manga.objects.get(id=comicId)
    if response.method == "POST":
        data = json.loads(response.body)
        if data["value"] == "Completed":
            currentChapter.lastRead = data['lastRead']
            currentChapter.read = True
            currentChapter.save()
        if data["value"] == "orientation":
            comic.orientation = data['orientation']
            comic.save()
        if data["value"] == "lastRead":
            currentChapter.lastRead = data['lastRead']
            currentChapter.save()

    if inLibrary == 1:
        ext = extension.objects.get(id=comic.source)
        sys.path.insert(0, ext.path)
        import source
        images = source.GetImageLinks(currentChapter.url)

    return render(response, "main/read.html", {"comic": comic, "chapter": currentChapter, "images": images})
    # return render(response, "main/read.html", {"comic": comic, "chapter": chapter})

def bypass(response, imageUrl):
    headers = {
        'Referer': "https://readmanganato.com/",
    }
    # r = requests.get(imageUrl, headers=headers)
    imageData = (requests.get(imageUrl, headers=headers)).content
    # print(imageData)
    return HttpResponse(imageData, content_type="image/png")
    # return HttpResponse("hello")