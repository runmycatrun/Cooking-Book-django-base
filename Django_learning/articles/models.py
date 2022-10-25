from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from transliterate import translit
from transliterate.exceptions import LanguageDetectionError
from random import randint
from django.db.models import Q


# Create your models here.
class ArticleQuerySet(models.QuerySet):
    def search(self, query=None):
        lookups = Q(title__icontains=query) | Q(content__icontains=query)
        return self.filter(lookups)


class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def search(self, query=None):
        return self.get_queryset().search(query=query)


class Article(models.Model):
    # https://docs.djangoproject.com/en/3.2/ref/models/fields/#field-types
    title = models.CharField(max_length=25)
    slug = models.SlugField(unique=True, max_length=50, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ArticleManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            try:
                slug = slugify(translit(str(self.title), reversed=True))
            except LanguageDetectionError:
                slug = slugify(self.title)

            def slug_check(slug):
                qs = Article.objects.filter(slug=slug).exclude(id=self.id)
                if qs.exists():
                    slug = f"{slug}-{self.id + randint(1000, 5000)}"
                    return slug_check(slug)
                else:
                    return slug

            slug = slug_check(slug)
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # return f"/articles/{self.slug}/"
        return reverse("article-detail", kwargs={'slug': self.slug})
