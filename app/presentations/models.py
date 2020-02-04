from django.db import models

# Create your models here.
class Presentation(models.Model):
	"""
	This model used to store the presentation data.
	"""

	elearning = models.CharField(max_length=500, help_text="elearning of the presentation")
	topic = models.CharField(max_length=500, help_text="topic of the presentation")
	slide = models.CharField(max_length=1000, help_text="name of the slide")
	is_demo = models.BooleanField(default=False)

	def __str__(self):
		return "%s - %s" % (self.topic, self.elearning)
