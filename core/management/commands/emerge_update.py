from django.core.management.base import BaseCommand
import os
from django.conf import settings
from apps.models import Product, Category

path = os.path.join(settings.STATIC_URL, r"core\img\product")

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

    def handle(self, *args, **options):
        for product in Product.objects.all():
            self.get_url(product)
            product.name = product.name.replace('/', ' ')
            product.save()
