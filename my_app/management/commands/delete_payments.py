from django.core.management.base import BaseCommand
import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class Command(BaseCommand):


    def handle(self, *args, **options):
        payments = stripe.PaymentIntent.list(limit=100)
        while payments:
            for payment in payments:
                if payment.status == "canceled":
                    stripe.PaymentIntent.cancel(payment.id)
            payments = stripe.PaymentIntent.list(limit=100)
