from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError

class Command(createsuperuser.Command):
    help = "Create a superuser with additional fields"

    def add_arguments(self, parser):
        parser.add_argument(
            '--first_name',
            dest='first_name',
            type=str,
            help='Specifies the first name for the superuser.'
        )
        parser.add_argument(
            '--last_name',
            dest='last_name',
            type=str,
            help='Specifies the last name for the superuser.'
        )
        parser.add_argument(
            "--email",
            dest='email',
            type=str,
            help='Species the email for the superuser'
        )
        parser.add_argument(
            "--username",
            dest='username',
            type=str,
            help='Species the username for the superuser'
        )
        parser.add_argument(
            "--password",
            dest='password',
            type=str,
            help='Species the password for the superuser'
        )


    def handle(self, *args, **options):
        first_name = options.get("first_name")
        last_name = options.get("last_name")
        display = options.get("username")
        email = options.get("email")
        password = options.get("password")

        if not display or not first_name or not last_name or not email or not password:
            raise CommandError("--email, --password, --username, --first_name, and --last_name are required")

        username = options.get("username").lower()

        self.UserModel._default_manager.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            display=display,
        )

        self.stdout.write("Superuser successfully created")


