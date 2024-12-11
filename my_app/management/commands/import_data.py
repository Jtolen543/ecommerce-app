from django.core.management.base import BaseCommand
import os
from django.conf import settings
import stripe
from ...models import Product, Category
import csv

path = os.path.join(settings.STATIC_URL, r"my_app\img\product")

store = {
    "Power Supply": os.path.join(path, "power_supply.png"),
    "Motherboard": os.path.join(path, "motherboard.png"),
    "Memory": os.path.join(path, "ram.png"),
    "Case": os.path.join(path, "case.png"),
    "Monitor": os.path.join(path, "monitor.png"),
    "Keyboard": os.path.join(path, "keyboard.png"),
    "Mouse": os.path.join(path, "mouse.png")
}

class Command(BaseCommand):
    help = "Tests the command creation"
    def get_url(self, product):
        spec = product.category.type
        if not store.get(spec):
            if spec == 'CPU':
                if product.name.find("Intel") != -1:
                    product.image = os.path.join(path, "intel_cpu.png")
                else:
                    product.image = os.path.join(path, "ryzen_cpu.png")
            elif spec == 'GPU':
                if product.name.find("NVIDIA") != -1:
                    product.image = os.path.join(path, "nvidia_gpu.png")
                else:
                    product.image = os.path.join(path, "radeon_gpu.png")
            elif spec == 'Storage':
                if product.description.find("SSD") != -1:
                    product.image = os.path.join(path, "ssd_storage.png")
                else:
                    product.image = os.path.join(path, "hdd_storage.png")
            elif spec == 'Cooling System':
                if product.description.find("liquid") != -1:
                    product.image = os.path.join(path, "liquid_cooling_system.png")
                else:
                    product.image = os.path.join(path, "fan_cooling_system.png")
        else:
            product.image = store[spec]

    def handle(self, *args, **kwargs):
        self.stdout.write("Please wait for the command to finish...")
        category_count = 0
        product_count = 0
        data_path = os.path.join(settings.STATIC_ROOT, r"my_app/data")
        with open(fr"{data_path}/categories.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not Category.objects.filter(type=row['type']).exists():
                    category = Category(type=row['type'])
                    category.save()
                    category_count += 1

        with open(fr"{data_path}\products.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not Product.objects.filter(name=row['name']).exists():
                    product = Product(
                        name=row['name'],
                        description=row['description'],
                        price=float(row['price']),
                        stock=int(row['stock']),
                        category=Category.objects.get(type=row["category"]),
                        is_active=True,
                    )
                    self.get_url(product)
                    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
                    stripe_product = stripe.Product.create(
                        name=product.name,
                        active=product.is_active,
                        description=product.description,
                    )
                    stripe_price = stripe.Price.create(
                        currency='usd',
                        product=stripe_product.id,
                        unit_amount=int(product.price * 100),
                        billing_scheme='per_unit',
                        nickname='Price Object for Product'
                    )
                    stripe.Product.modify(
                        stripe_product.id,
                        default_price=stripe_price.id
                    )
                    product.product_id = stripe_product.id
                    product.save()
                    product_count += 1
        self.stdout.write(f"Successfully added {category_count} categories to the database and Stripe dashboard")
        self.stdout.write(f"Successfully added {product_count} products to the database and Stripe dashboard")
