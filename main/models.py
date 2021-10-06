from django.db import models

# Create your models here.

"""
manga cover needs to be downloaded,
should be downloaded to a manga directory and given a unique identifier

i have chosen the identifier to be a md5 hash so that there are no two identical identifiers

the identifier is then assigned like so manga [ cover: identieer]
"""

class manga(models.Model):
	title = models.TextField(default='', blank=True)
	cover = models.TextField(default='', blank=True)

	options = [
	('Manga', 'Manga'),
	('Novel', 'Novel')
	]
	type = models.CharField(max_length=6,choices=options, default='Manga')
	description = models.TextField(default=None, blank=True)
	chapters = models.TextField(default='',blank=True,max_length=None)
	categories = models.TextField(default="All,")
	source = models.TextField(default="", blank=True)
	
	def __str__(self):
		return self.title

class sources(models.Model):
	name = models.TextField(default='', blank=True)

	def __str__(self):
		return self.name

class categories(models.Model):
	name = models.TextField(default='', blank=True)

	def __str__(self):
		return self.name