from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.models import Product, Category

@receiver(post_save, sender=Product)
def update_category_count_on_save(sender, instance, **kwargs):
    category = instance.category
    category.count = category.products.count()
    category.save()

@receiver(post_delete, sender=Product)
def update_category_count_on_delete(sender, instance, **kwargs):
    category = instance.category
    category.count = category.products.count()
    category.save()
