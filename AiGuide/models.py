from django.db import models
from User.models import User

class Thread(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    thread_name = models.CharField(max_length=100)
    thread_id = models.CharField(max_length=100)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.thread_id

    def get_messages(self):

        return ThreadMessage.objects.filter(thread=self)
    
    def create_new_message(self, sent_by, message_content):

        new_thread_message = ThreadMessage(thread=self, message_content=message_content)
        
        if sent_by == "ai":
            new_thread_message.is_ai_message = True
        elif sent_by == "user":
            new_thread_message.is_user_message = True

        new_thread_message.save()

class ThreadMessage(models.Model):

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    is_user_message = models.BooleanField(default=False)
    is_ai_message = models.BooleanField(default=False)

    message_content = models.JSONField()
    sent_when = models.DateTimeField(auto_now_add=True)