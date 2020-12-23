from django.contrib.auth.models import AbstractBaseUser,    BaseUserManager, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from config.common import STRIPE_SECRET_KEY


class UserManager(BaseUserManager):

	def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
		if not email:
			raise ValueError('Users must have an email address')
		now = timezone.now()
		email = self.normalize_email(email)
		user = self.model(
			email=email,
			is_staff=is_staff,
			is_active=True,
			is_superuser=is_superuser,
			last_login=now,
			date_joined=now,
			**extra_fields
		)
		user.set_password(password)

		user.save(using=self._db)
		return user

	def create_user(self, email, password, **extra_fields):
		return self._create_user(email, password, False, False, **extra_fields)

	def create_superuser(self, email, password, **extra_fields):
		user=self._create_user(email, password, True, True, **extra_fields)
		user.save(using=self._db)
		return user


class User(AbstractBaseUser, PermissionsMixin):

	MEMBER_TYPE = (("Team Member", "Team Member"), ("Manager", "Manager"),)
	email = models.EmailField(max_length=254, unique=True)
	name = models.CharField(max_length=254,null=True,blank=True)
	username = models.CharField(max_length=254, help_text="username of the user")
	surname = models.CharField(max_length=254, help_text="surname of the user")
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	last_login = models.DateTimeField(null=True, blank=True)
	date_joined = models.DateTimeField(auto_now_add=True)
	timezone = models.CharField(max_length=100, default='UTC')
	is_demo = models.BooleanField(default=False)
	manager = models.EmailField(max_length=254, null=True, blank=True)
	member_type = models.CharField(max_length=254, choices=MEMBER_TYPE, default=[0][0])
	stripe_customer = JSONField(default=dict, null=True, blank=True)

	USERNAME_FIELD = 'email'
	EMAIL_FIELD = 'email'
	REQUIRED_FIELDS = []

	objects = UserManager()

	def get_absolute_url(self):
		return "/users/%i/" % (self.pk)

	@property
	def elearnigs(self):
		from elearning.models import ELearningUserSession
		return ELearningUserSession.objects.filter(user=self)

	def save(self, *args, **kwargs):
		"""
        Overrides default save to make sure:
        """

		# create a strip customer when one is not available
		if not self.stripe_customer:
			self.create_stripe_customer()

		super(User, self).save(*args, **kwargs)

	def create_stripe_customer(self, source_token=None):
		import stripe

		if not self.stripe_customer:
			stripe.api_key = STRIPE_SECRET_KEY

			try:
				params = {'email': self.get_username()}

				if source_token:
					token_id = source_token['id']
					params['source'] = token_id

				self.stripe_customer = stripe.Customer.create(**params)
				self.save()
			except Exception as e:
				raise ObjectDoesNotExist('Error creating stripe customer: %s', e.__str__())
