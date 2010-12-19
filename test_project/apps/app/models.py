from django.db import models


class Item(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=150)

    def __unicode__(self):
        return self.title
