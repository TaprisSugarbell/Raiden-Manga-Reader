from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import manga, extension
from main.Backend.extensions.extension_list import ext_list
# from .reader import * # This line is currently not needed
# Create your views here.

def redirect_view(response):
    response = redirect('/library')
    return response

def library(response):
    library = manga.objects.all
    return render(response, "main/library.html", {'library': library})

def browse(response):
    return render(response, "main/browse.html")

def extensions(response):
    all_extensions = ext_list()
    installed_extensions = extension.objects.all
    return render(response, "main/extensions.html", {'installed': installed_extensions, 'all': all_extensions})

def novel(response, id):
    # content = epub2text('E:\Abdullah\Code\Python\Computer Science  NEA\master\Shogan-Manga-Reader-main\main\book2.epub')
    novel = manga.objects.get(id=id)
    return render(response, "main/novel.html", {"novel":novel})

def comic(response, id):
    comic = manga.objects.get(id=id)
    return render(response, "main/comic.html", {"comic":comic})
