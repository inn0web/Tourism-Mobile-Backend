from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from Places.models import City

class Blog(models.Model):

    title = models.CharField(max_length=225)
    thumbnail = models.FileField(upload_to='blog/thumbnail')
    city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL)
    content = CKEditor5Field('Text', config_name='extends', null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_images(self):

        return [blog_image.image.url for blog_image in BlogImage.objects.filter(blog=self)]

class BlogImage(models.Model):

    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    image = models.FileField(upload_to='blog/images')
    uploaded_at = models.DateTimeField(auto_now_add=True)