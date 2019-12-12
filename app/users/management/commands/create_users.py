from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = 'create the users'

    def add_arguments(self, parser):
        parser.add_argument('user_ids', nargs='+', type=int)

    def handle(self, *args, **options):

        for users_count in range(1, options['user_ids'][0]):
            user_data = {
                        "email": "admin"+str(users_count)+"@gmail.com",
                        "password":"spider@123",
                        "username":"admin"+str(users_count),
                        "surname":"admin"+str(users_count),
                        "is_superuser": False,
                        "is_staff": False,
                     }
            User.objects._create_user(**user_data)

        self.stdout.write(self.style.SUCCESS('Successfully Created users "%s"' % options['user_ids'][0]))