import os
from django.conf import settings
from .models import Location, UserLocation, Category, ProductOrders, Product, Order
import stripe
import random



def location_exists(form):
    if isinstance(form, stripe._payment_intent.PaymentIntent.Shipping.Address):
        try:
            existing_location = Location.objects.get(
                address=form.line1,
                details=form.line2,
                city=form.city,
                state=form.state,
                zipcode=form.postal_code,
                country=form.country
            )
        except:
            return False
    else:
        try:
            existing_location = Location.objects.get(
                address=form.cleaned_data['address'],
                details=form.cleaned_data['details'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                zipcode=form.cleaned_data['zipcode'],
                country=form.cleaned_data['country']
            )
        except:
            return False
    return existing_location


def user_location_exists(location, user):
    try:
        existing_user_loc = UserLocation.objects.get(
            user=user,
            location=location
        )
    except:
        return False
    return existing_user_loc


def update_user_location(form, user, location, is_primary):
    try:
        existing_location = Location.objects.get(
            address=form.cleaned_data['address'],
            details=form.cleaned_data['details'],
            city=form.cleaned_data['city'],
            state=form.cleaned_data['state'],
            zipcode=form.cleaned_data['zipcode'],
            country=form.cleaned_data['country']
        )
    except:
        existing_location = None
    if not existing_location:
        existing_location = Location(
            address=form.cleaned_data['address'],
            details=form.cleaned_data['details'],
            city=form.cleaned_data['city'],
            state=form.cleaned_data['state'],
            zipcode=form.cleaned_data['zipcode'],
            country=form.cleaned_data['country']
        )
        existing_location.save()

    user_location = UserLocation.objects.get(
        user_id=user,
        location_id=location
    )

    if user_location:
        user_location.location = existing_location
        user_location.is_primary = is_primary
        user_location.save()
    return user_location

def parse_payments(payments):
    parsed = []
    available = ['visa', 'american_express', 'mastercard', 'discover']
    for payment in payments:
        brand = payment['card']['brand']
        new_dict = {
            "id": payment["id"],
            "customer": payment["customer"],
            "last4": payment['card']['last4'],
            "brand": brand.replace("_", " ").title(),
            "image": f"{settings.STATIC_URL}my_app/img/{brand}.svg" if brand in available else f"{settings.STATIC_URL}my_app/img/default.svg",
            "type": payment["type"].replace("_", " ").title(),
            "name": payment["billing_details"]["name"],
            "exp_date": str(payment["card"]["exp_month"]) + "/" + str(payment["card"]["exp_year"])
        }
        temp = payment["billing_details"]["address"]
        new_dict["address"] = f"{temp['line1']} {temp['line2'] if temp['line2'] else ''}".strip()
        new_dict["locale"] = f"{temp['city']}, {temp['state']}, {temp['postal_code']} ,{temp['country']}"
        parsed.append(new_dict)
    parsed.reverse()
    return parsed

def product_packager(product):
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    stripe_product = stripe.Product.create(
        name=product.name,
        active=product.is_active,
        description=product.description,
    )
    stripe_price = stripe.Price.create(
        currency='usd',
        product = stripe_product.id,
        unit_amount=int(product.price * 100),
        billing_scheme = 'per_unit',
        nickname='Price Object for Product'
    )
    stripe.Product.modify(
        stripe_product.id,
        default_price = stripe_price.id
    )
    product.product_id = stripe_product.id
    product.save()

def randomize_carousel():
    laptops, tablets, smartphones  = [], [], []
    loop1 = list(Category.objects.get(type="GPU").products.all())
    loop2 = list(Category.objects.get(type="CPU").products.all())
    loop3 = list(Category.objects.get(type="Monitor").products.all())
    while len(laptops) != 8:
        idx = random.randrange(0, len(loop1))
        laptops.append(loop1[idx])
        loop1.pop(idx)
    while len(tablets) != 8:
        idx = random.randrange(0, len(loop2))
        tablets.append(loop2[idx])
        loop2.pop(idx)
    while len(smartphones) != 8:
        idx = random.randrange(0, len(loop3))
        smartphones.append(loop3[idx])
        loop3.pop(idx)
    return laptops, tablets, smartphones

def calculate_tax(line_items, location=None):
    if type(location) == str:
        address = {"ip_address": location}
    elif type(location) == dict:
        address = {
            "address": location,
            "address_source": "shipping"
        }
    else:
        address = {
            "address": {
                "line1": location.address if location else "920 5th Ave",
                "line2": location.details if location else '',
                "city": location.city if location else "Seattle",
                "state": location.state if location else "WA",
                "postal_code": location.zipcode if location else "98104",
                "country": location.country if location else "US",
            },
            "address_source": "shipping",
        }

    summary = stripe.tax.Calculation.create(
        currency="usd",
        customer_details=address,
        line_items=line_items,
        shipping_cost={"amount": 2500},
        expand=["line_items"]
    )

    result = {
        "total": round(summary["amount_total"] / 100, 2),
        "shipping": round(summary["shipping_cost"]["amount"] / 100, 2),
        "tax": round(summary["tax_amount_exclusive"] / 100, 2),
        "subtotal": sum(round(item['amount'] / 100, 2) for item in summary["line_items"]['data'])
    }
    return result



def order_number_generator():
    current = Order.objects.all().last()
    if current:
        current_id = current.order_id
        data = [int(num) for num in current_id.split('-')]
        segment_1, segment_2, segment_3, = data
        if segment_3 < 9999999:
            segment_3 += 1
        else:
            segment_3 = 0
            segment_2 += 1
        if segment_2 > 9999999:
            segment_2 = 0
            segment_1 += 1
        if segment_1 > 999:
            print("Order numbers have been filled, will overflow into first segment until resolved")
        return f"{segment_1:03}-{segment_2:07}-{segment_3:07}"

    else:
        return "000-0000000-0000001"


# def package_locations(locations):
#     result = []
#     for location in locations:
#         location = location.location
#         street = location.address + location.details
#         address = f"{street.strip()}, {location.city}, {location.state}, {location.zipcode}, {location.country}"
#         result.append(address)
#     return result


# Build a clean-up function
# def cleanup_database():
#     unused_locations = db.session.query(Location).outerjoin(UserLocation).filter(UserLocation.location_id == None).all()
#     for location in unused_locations:
#         db.session.delete(location)
#     print(f"Removed {unused_locations.size()} locations from the {Location.__tablename__} table")
#     unused_associations = db.session.query(UserLocation).filter(UserLocation.location_id == None).all()
#     for association in unused_associations:
#         association.delete(synchronize_session=False)
#     print(f"Removed {unused_associations.size()} associations from the {UserLocation.__tablename__} table")
#
#     print("Clean up has been successful")