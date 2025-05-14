from django.db import models

class Advertisement(models.Model):
    title = models.CharField(max_length=200)  # "Luxury vehicles at 10% discount"
    subtitle = models.TextField(blank=True)  # "Get a ride at a discounted rate when you use our services."
    image = models.FileField(upload_to='advertisements/')  # The vehicle image
    button_text = models.CharField(max_length=50, default="Book now")  # "Book now"
    button_url = models.URLField() 
    start_date = models.DateTimeField()  
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True) 
    priority = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title