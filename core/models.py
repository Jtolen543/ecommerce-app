import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import stripe
from django.db.models import TextField, ImageField, DecimalField, BooleanField, ForeignKey, IntegerField, \
    PositiveIntegerField, DateTimeField, CharField, ManyToManyField
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        first_name = extra_fields.pop("first_name", None)
        last_name = extra_fields.pop("last_name", None)
        display = extra_fields.pop("display", None)

        user = self.model(username=username,
                          email=email,
                          first_name=first_name,
                          last_name=last_name,
                          display=display,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

# Create your models here.
class UserLocation(models.Model):
    user = ForeignKey('User', on_delete=models.CASCADE, related_name="user")
    location = ForeignKey('Location', on_delete=models.CASCADE, related_name="location")
    is_primary = BooleanField(default=False)
    objects = models.Manager()
    class Meta:
        unique_together = (("user", "location"),)
        db_table = "user_locations"


class User(AbstractUser):
    first_name = TextField(null=False)
    last_name = TextField(null=False)
    display = TextField(unique=True, null=False)
    username = TextField(unique=True, null=False)
    phone = TextField(null=True)
    email = TextField(unique=True, null=False)
    password = TextField(null=False)
    birth_date = TextField(null=True)
    locations = models.ManyToManyField("Location", through="UserLocation", related_name="users")
    objects = UserManager()

    def save(self, *args, **kwargs):
        super().save()
        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
        customer = stripe.Customer.search(query=f"email: '{self.email}'")
        if not customer['data']:
            stripe.Customer.create(
                name=f"{self.first_name} {self.last_name}",
                email=self.email,
                phone=self.phone,
            )
    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self._meta.fields}

    class Meta:
        db_table = "users"


class Location(models.Model):
    address = TextField(null=False)
    details = TextField(null=True)
    city = TextField(null=False)
    state = TextField(null=False)
    zipcode = TextField(null=False)
    country = TextField(null=False)
    objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['address', 'details', 'city', 'state', 'zipcode', 'country'],
                name='uix_street_address'
            )
        ]
        db_table = "locations"

    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self._meta.fields}

class Category(models.Model):
    type = TextField(unique=True)
    count = IntegerField(default=0)
    objects = models.Manager()
    class Meta:
        db_table = "categories"

class Product(models.Model):
    name = TextField(unique=True)
    description = TextField()
    price = DecimalField(decimal_places=2, max_digits=10)
    stock = PositiveIntegerField()
    product_id = TextField(null=True)
    image = ImageField(upload_to="product")
    category = ForeignKey(to="Category", on_delete=models.CASCADE, related_name="products")
    is_active = BooleanField(default=True)
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)
    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save()

    class Meta:
        db_table = "products"

class Order(models.Model):
    order_id = TextField(unique=True)
    stripe_id = TextField(unique=True)
    customer = ForeignKey(to="User", on_delete=models.CASCADE, related_name="orders", null=True)
    products = models.ManyToManyField(to="Product", through="ProductOrders", related_name="orders")
    name = TextField(null=True)
    total_price = DecimalField(max_digits=10, decimal_places=2, default=0)
    objects = models.Manager()
    location = ForeignKey(to="Location", on_delete=models.CASCADE, related_name="orders", null=True)
    created = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = timezone.now()
        super().save()

    class Meta:
        db_table = "orders"


class ProductOrders(models.Model):
    product = ForeignKey(Product, on_delete=models.CASCADE)
    order = ForeignKey(Order, on_delete=models.CASCADE)
    quantity = IntegerField(default=0)
    price = DecimalField(max_digits=10, decimal_places=2, default=0)
    objects = models.Manager()


    class Meta:
        unique_together = ("product", "order")
        db_table = "product_orders"



