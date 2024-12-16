from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from .models import UserLocation, Product, Category, ProductOrders, Order
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from .shopping_cart import ShoppingCart
from ipware import get_client_ip
from .forms import *
from .helper import (location_exists, user_location_exists, update_user_location, parse_payments, product_packager,
                     randomize_carousel, calculate_tax, order_number_generator)
from .countries import reverse_country_dict
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import os
import stripe
import json
import re


current_year = timezone.now().year
serializer = default_token_generator
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

def home(request):
    laptops, tablets, smartphones = randomize_carousel()
    categories = {
        'GPUs': laptops,
        'CPUs': tablets,
        'Monitors': smartphones
    }
    context = {'title': "", 'current_year': current_year, "user": request.user, 'categories': categories}
    return render(request, "my_app/home.html", context=context)

def about(request):
    context = {'title': "", 'current_year': current_year, "user": request.user}
    return render(request, "my_app/about.html", context=context)

@csrf_protect
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            send_mail(
                subject=form.cleaned_data['subject'],
                message=f"Message from {form.cleaned_data['name'].title()}\n\n{form.cleaned_data['message']}",
                from_email=os.environ.get("DJANGO_EMAIL_ADDRESS"),
                recipient_list=[form.cleaned_data['email']]
            )
            messages.success(request, "Message has been successfully sent")
            return redirect('contact')
        else:
            messages.error(request, "Form must be filled out")
    else:
        form = ContactForm()
    context = {'title': "", 'current_year': current_year, "user": request.user, 'form': form, 'key':os.environ.get("GOOGLE_MAPS_KEY")}
    return render(request, "my_app/contact.html", context=context)

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            if User.objects.filter(username=form.data['username'].lower()).exists():
                form.add_error('username', "This username has already been taken.")

            elif User.objects.filter(email= form.data['email']).exists():
                form.add_error('email', "This email has already been registered, please consider loging in")
            else:
                new_user = User(
                    first_name= form.cleaned_data['first_name'].title(),
                    last_name=form.cleaned_data['last_name'].title(),
                    display=form.cleaned_data['username'],
                    username=form.cleaned_data['username'].lower(),
                    email=form.cleaned_data['email'],
                    password=make_password(form.cleaned_data['password']),
                    phone=form.cleaned_data['phone'].strip().replace(' ', '-')
                )
                new_user.save()
                messages.success(request, "Account has been successfully Created!")
                return redirect('login')
    else:
        form = RegisterForm()
    return render(request,"my_app/auth/signup.html", {"form":form, "title":"Sign-Up", "current_year":current_year})


def tos(request):
    return render(request,"my_app/tos.html", {"current_year":current_year})


def signin(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email= form.cleaned_data['email'].lower()).first()
            if not user:
                user = User.objects.filter(username=form.cleaned_data['email'].lower()).first()
            if user:
                user = authenticate(username=user.username, password=form.cleaned_data['password'])
                if user:
                    login(request, user)
                    return redirect("home")
                else:
                    messages.error(request, "Password is incorrect. Please try Again")
            else:
                messages.error(request, "Username or Email does not exist. Consider creating an account")
    else:
        form = LoginForm()
    context = {"form":form, "title": "Sign-In", "current_year": current_year}
    return render(request, 'my_app/auth/signin.html', context=context)


@login_required
def signout(request):
    logout(request)
    return redirect("home")


def reset_password(request):
    if request.method == "POST":
        form = ResetForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email= form.cleaned_data['email']).first()
            if not user:
                user = User.objects.filter(username= form.cleaned_data['email'].lower()).first()
            if user:
                token = serializer.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                link = request.build_absolute_uri(
                    reverse('set_password', kwargs={'uidb64': uidb64, 'token': token})
                )
                # No need to provide username/password, django automatically searches for it in settings
                send_mail(
                    subject="Reset Link",
                    from_email=os.environ.get("DJANGO_EMAIL_ADDRESS"),
                    message=f"Click this to reset the password to your account. This link will expire in 5 minutes\n\n{link}",
                    recipient_list=[user.email]
                )
                messages.success(request,f"Password Reset Link has been sent to {form.cleaned_data['email']}.")
            else:
                messages.error(request,"Email does not exist.")
        else:
            messages.error(request, "Please fill out the form")
    else:
        form = ResetForm()
    return render(request,'my_app/auth/reset_password.html', {"form":form, "current_year":current_year, "title":"Reset"})


def set_password(request, uidb64, token):
    try:
        new_id = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=new_id)
    except (TypeError, ValueError, OverflowError):
        user = None
    if user and request.method == "POST" and serializer.check_token(user, token):
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Password has been successfully updated!")
            return redirect('login')
        else:
            messages.error(request, "Please fill out the form")
    else:
        form = SetNewPasswordForm()
    context = {"form":form, "current_year":current_year, "title":"Reset", "token": token, 'uidb64': uidb64}
    return render(request, "my_app/auth/set_password.html", context=context)


@login_required
def profile_account(request):
    infos = ["first_name", "last_name", "email", "phone", "username"]
    user = request.user
    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if form.is_valid():
            for info in infos:
                setattr(user, info, form.cleaned_data[info])
                if info == 'username':
                    user.display = user.username
                    user.username = user.username.lower()
                elif info == "phone":
                    formatted_phone = form.cleaned_data['phone'].strip().replace(" ", "-")
                    user.phone = formatted_phone
            user.birth_date = form.cleaned_data['birth_date']
            user.save()
            messages.success(request,"Changes have been successfully saved")
    initial = {}
    for info in infos:
        if info == "username":
            initial[info] = user.display
        else:
            initial[info] = getattr(user, info)
    initial['birth_date'] = user.birth_date if user.birth_date else ""
    form = EditProfileForm(initial=initial)
    context = {"user":user, "form":form, "title":"Account"}
    return render(request,"my_app/profile/account.html", context=context)
#
#
@login_required
def profile_location(request):
    user = request.user
    locations = user.locations.all()
    paginator = Paginator(locations, 5)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(paginator.num_pages)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    context = {"user":user, "title":"Location", "key":os.environ.get("GOOGLE_MAPS_KEY"), "page_obj":page_obj}
    return render(request,"my_app/profile/location.html", context=context)


@login_required
def add_address(request):
    codes = ["address", "details", "city", "state", "zipcode", "country"]
    link = reverse('add_address')
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            location = location_exists(form)
            if not location:
                location = Location()
                for code in codes:
                    setattr(location, code, form.cleaned_data[code])
                location.save()
            association = user_location_exists(location, request.user)
            if not association:
                association = UserLocation(
                    user=request.user,
                    location=location,
                    is_primary=False
                )
                association.save()

            messages.success(request,"Address have been successfully added")
            return redirect('locations')
    else:
        form = LocationForm()
    context = {"form":form, "current_year":current_year, "title":"Add Address",
                           "key":os.environ.get("GOOGLE_MAPS_KEY"), "link":link}
    return render(request, "my_app/profile/address.html", context=context)


@login_required
def edit_address(request, _id):
    loc = Location.objects.get(pk=_id)
    fields = ["address", "details", "city", "state", "zipcode", "country"]
    link = reverse('edit_address', kwargs={"_id": _id})
    if request.method == "POST":
        form = LocationForm(request.POST)

        if form.is_valid():
            update_user_location(form, request.user, loc, False)

            messages.success(request,"Address has been successfully updated")
            return redirect('locations')

    else:
        initial = {field: getattr(loc, field) for field in fields}
        initial['country'] = reverse_country_dict[initial['country']]
        form = LocationForm(initial=initial)

    context = {"form":form, "current_year":current_year, "title":"Edit Address", "key":os.environ.get("GOOGLE_MAPS_KEY"), "link":link}
    return render(request,"my_app/profile/address.html", context=context)


@login_required
def delete_address(request, _id):
    loc = Location.objects.get(pk=_id)
    association = UserLocation.objects.get(user=request.user, location=loc)
    association.delete()
    messages.success(request, "Address has been successfully removed")
    return redirect("locations")


@login_required
def profile_payment(request):
    customer = stripe.Customer.search(query=f"email: '{request.user.email}'")
    payments = stripe.Customer.list_payment_methods(customer.data[0]['id'])['data']
    payments = parse_payments(payments)

    paginator = Paginator(payments, 5)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(paginator.num_pages)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {"user":request.user, "title":"Wallet", "page_obj": page_obj}
    return render(request, 'my_app/profile/payments.html', context=context)

@login_required
def add_payment(request):
    context = {'title': "Add Payment", 'current_year': current_year}
    return render(request, "my_app/profile/payments/add_payment.html", context=context)

@login_required
def create_setup_intent(request):
    customer = stripe.Customer.search(query=f"email: '{request.user.email}'")
    setup = stripe.SetupIntent.create(
        payment_method_types=["card", "us_bank_account"],
        customer=customer.data[0]['id'],
    )
    link = request.build_absolute_uri(reverse('payments'))
    data = {"public_key":os.environ.get("STRIPE_PUBLISHABLE_KEY"),
               'client_secret':setup['client_secret'], 'link':link}
    return JsonResponse(data)

@login_required
def edit_payment(request, pm_id):
    customer = stripe.Customer.search(query=f"email: '{request.user.email}'")
    if request.method == "POST":
        form = PaymentLocationForm(request.POST)
        if form.is_valid():
            data = {
                "city":form.cleaned_data["city"],
                "country": form.cleaned_data["country"],
                "line1": form.cleaned_data["address"],
                "line2": form.cleaned_data["details"],
                "postal_code": form.cleaned_data["zipcode"],
                "state": form.cleaned_data["state"]
            }
            stripe.PaymentMethod.modify(
                pm_id,
                billing_details={"address": data}
            )
            return redirect("payments")
    else:
        payment = stripe.Customer.retrieve_payment_method(
            customer=customer.data[0]["id"],
            payment_method=pm_id
        )
        initial = {
            "city": payment["billing_details"]["address"]["city"],
            "address": payment["billing_details"]["address"]["line1"],
            "details": payment["billing_details"]["address"]["line2"],
            "state": payment["billing_details"]["address"]["state"],
            "country": reverse_country_dict[payment["billing_details"]["address"]["country"]],
            "zipcode": payment["billing_details"]["address"]["postal_code"],
            "month": payment["card"]["exp_month"],
            "year": payment["card"]["exp_year"],
        }
        form = PaymentLocationForm(initial=initial)
    link = request.build_absolute_uri(reverse("edit_payment", kwargs={"pm_id": pm_id}))
    context = {'title': "Edit Payment", "public_key": os.environ.get("STRIPE_PUBLISHABLE_KEY"),
            'link': link, "user": request.user, 'key':os.environ.get("GOOGLE_MAPS_KEY"), "form": form}
    return render(request, "my_app/profile/payments/edit_payment.html", context=context)

@login_required
def delete_payment(request, pm_id):
    stripe.PaymentMethod.detach(pm_id)
    messages.success(request, "Payment method has been removed from wallet")
    return redirect("payments")

@login_required
def profile_orders(request):
    user = request.user
    orders = user.orders.all()
    information = []

    for order in orders:
        new_dict = {}
        address = order.location.to_dict()
        address['line1'] = address['address']
        address['line2'] = address['details']
        del address['address']
        del address['details']
        address.update({"name": order.name})
        new_dict.update({"address": address})

        products = ProductOrders.objects.filter(order=order)
        new_dict.update({"products": products})
        information.append((order, new_dict))

    paginator = Paginator(information, 6)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(paginator.num_pages)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {"user": user, "title": "Orders", "page_obj": page_obj}
    return render(request, "my_app/profile/orders/orders.html", context=context)


@login_required
@staff_member_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            if Product.objects.filter(name=form.cleaned_data['name']).exists():
                messages.error(request, "Product already exists")
            else:
                category = Category.objects.filter(type=form.cleaned_data['category'].title())
                if not category.exists():
                    category = Category(type=form.cleaned_data['category'].title())
                    category.save()
                else:
                    category = category.first()
                # Product and Price Creation
                item = Product(
                    name=form.cleaned_data['name'].title(),
                    description=form.cleaned_data['description'],
                    price=form.cleaned_data['price'],
                    stock=form.cleaned_data['stock'],
                    image=form.cleaned_data['image'],
                    is_active=form.cleaned_data['is_active'],
                    category=category
                )
                category.save()
                product_packager(item)
                return redirect("admin")
        else:
            messages.error(request, "Form needs to be filled out")
    else:
        form = ProductForm()
    context = {'title': "Add Product", 'current_year': current_year, "user": request.user, 'form':form}
    return render(request, 'my_app/admin/add_product.html', context=context)

@login_required
def delete_account(request):
    context = {"user": request.user, "title": "Delete Account"}
    return render(request, 'my_app/profile/delete_account.html', context=context)


@login_required
@staff_member_required
def edit_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            pass
    else:
        form = ProductForm()
    context = {'title': "Edit Product", 'current_year': current_year, "user": request.user, 'form':form}
    return render(request, 'my_app/admin/edit_product.html', context=context)

@csrf_protect
def product(request, name):
    if request.method == "POST":
        cart = ShoppingCart(request)
        if not cart.add_to_cart(name, int(request.POST['quantity'])):
            messages.error(request, "Cannot add more of this item")

    item = Product.objects.get(name=name)
    context = {'title': "Product", 'current_year': current_year, 'user': request.user, 'product':item}
    return render(request, 'my_app/product/page.html', context=context)

def shop_cart(request):
    cart = ShoppingCart(request)
    products, subtotal = cart.get_shopping_list()
    addition = {'shipping': 0, 'tax': 0, 'total': 0}

    client_ip, is_routable = get_client_ip(request)
    if not is_routable:
        client_ip = None
    line_items = [{"amount": int(item['price'] * 100) * item["quantity"],
                   "reference": item["name"]} for item in products]

    if line_items:
        addition = calculate_tax(line_items)
    context = {'title': "Product", 'current_year': current_year, 'user': request.user, 'products': products,
               'subtotal': subtotal, "root": request.get_host()} | addition
    return render(request, 'my_app/product/checkout.html', context=context)

@csrf_protect
def update_cart(request, name, quantity):
    cart = ShoppingCart(request)
    cart.update_cart(name, quantity)
    products, subtotal = cart.get_shopping_list()

    client_ip, is_routable = get_client_ip(request)
    if not is_routable:
        client_ip = None

    line_items = [{"amount":int(item['price'] * 100) * item['quantity'],
                   "reference": item["name"]} for item in products]
    data = calculate_tax(line_items, client_ip)
    data['cart'] = cart.total_items()

    return JsonResponse(data)

def delete_item(request, name):
    cart = ShoppingCart(request)
    cart.delete_item(name)
    return redirect('shop_cart')

def session_checkout(request):
    if request.user.is_authenticated:
        return redirect('confirm_checkout')
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            if form.is_valid():
                user = User.objects.filter(email=form.cleaned_data['email']).first()
                if not user:
                    user = User.objects.filter(username=form.cleaned_data['email'].lower()).first()
                if user:
                    user = authenticate(username=user.username, password=form.cleaned_data['password'])
                    if user:
                        login(request, user)
                        return redirect("confirm_checkout")
                    else:
                        messages.error(request, "Password is incorrect. Please try Again")
                else:
                    messages.error(request, "Username or Email does not exist. Consider creating an account")
        else:
            messages.error(request, "Please fill out the form")

    else:
        form = LoginForm()

    context = {"form":form, "title": "Guest Checkout", "current_year": current_year}
    return render(request,"my_app/checkout/session_checkout.html", context=context)

@csrf_protect
def confirm_checkout(request):
    cart = ShoppingCart(request)

    products, subtotal = cart.get_shopping_list()
    context = {'title': "Confirm Checkout", 'current_year': current_year, 'products': products, 'subtotal': 0,
               'total': 0, 'tax': 0, 'shipping': 0, "user": request.user}
    if request.user.is_authenticated:
        if request.method == "POST":
            form = CheckoutAddressForm(request.POST)
            if form.is_valid():
                location = location_exists(form)
                if not location:
                    location = Location()
                    codes = ["address", "details", "city", "state", "zipcode", "country"]
                    for code in codes:
                        setattr(location, code, form.cleaned_data[code])
                    location.save()
                association = user_location_exists(location, request.user)
                if not association:
                    association = UserLocation(
                        user=request.user,
                        location=location,
                        is_primary=False
                    )
                    association.save()
                return redirect('confirm_checkout')
        form = CheckoutAddressForm()
        address_form = SelectAddressForm(user=request.user)
        customer = stripe.Customer.search(query=f"email: '{request.user.email}'")
        payments = stripe.Customer.list_payment_methods(customer.data[0]["id"])
        payments = parse_payments(payments)
        additional = {'address_form':address_form, 'payments':payments, 'form':form, 'key': os.environ.get("GOOGLE_MAPS_KEY")}
        context.update(additional)
    return render(request, "my_app/checkout/confirm_checkout.html", context=context)


def finalize_express_checkout(request, pi_id, email):
    stripe.PaymentIntent.confirm(
        pi_id,
        return_url=request.build_absolute_uri(reverse("payment_success", kwargs={"pi_id": pi_id})),
        receipt_email=email
    )
    return redirect(reverse("payment_success", kwargs={"pi_id": pi_id}))


def payment_success(request, pi_id):
    cart = ShoppingCart(request)
    products = cart.get_shopping_list()[0]

    payment = stripe.PaymentIntent.retrieve(pi_id)
    if Order.objects.filter(stripe_id=pi_id).exists():
        context = {'title': "Review Order", 'current_year': current_year, "user": request.user,
                   "order_num": Order.objects.get(stripe_id=pi_id).order_id, "total": payment.amount / 100}
    else:
        order_num = order_number_generator()
        try:
            stripe.PaymentIntent.modify(pi_id, metadata={"order_number": order_num})
            if not location_exists(payment['shipping']['address']):
                address = payment['shipping']['address']
                location = Location(
                    address=address['line1'],
                    details=address['line2'],
                    city=address['city'],
                    state=address['state'],
                    zipcode=address['postal_code'],
                    country=address['country'],
                )
                location.save()
            else:
                location = Location.objects.get(address=payment.shipping.address.line1)

            order = Order(
                order_id=order_num,
                stripe_id=pi_id,
                customer=request.user if request.user.is_authenticated else None,
                total_price=payment.amount / 100,
                name=payment['shipping']['name'],
                location=location
            )
            order.save()

            for item in products:
                _product = Product.objects.get(name=item["name"])
                product_order = ProductOrders(
                    product=_product,
                    order=order,
                    quantity=item['quantity'],
                    price= item['price']
                )
                product_order.save()
            context = {'title': "Review Order", 'current_year': current_year, "user": request.user,
                       "order_num": order_num, "total": payment.amount / 100}
            cart.clear_cart()
        except stripe.InvalidRequestError:
            return HttpResponseNotFound("<h1>Invalid Checkout Session</h1>")
    return render(request, "my_app/checkout/payment_success.html", context=context)

def review_order(request, order_num):
    order = Order.objects.get(order_id=order_num)
    payment = stripe.PaymentIntent.retrieve(order.stripe_id)
    payment_method = parse_payments([stripe.PaymentMethod.retrieve(payment.payment_method)])[0]
    order_products = ProductOrders.objects.filter(order=order)

    tax = int(payment["metadata"]["tax"]) / 100
    subtotal = int(payment["metadata"]["subtotal"]) / 100
    shipping = int(payment["metadata"]["shipping"]) / 100

    context = {'title': "Review Order", 'current_year': current_year, "user": request.user, "order": order,
               'method': payment_method, 'address': payment["shipping"]["address"], "products": order_products,
               'order_num': order_num, 'date': order.created.strftime("%B %d, %Y"), "tax":tax,
               'subtotal': subtotal, 'shipping':shipping, 'total': payment['amount'] / 100}
    return render(request, "my_app/checkout/order_summary.html", context=context)


def delete_user_account(request):
    user = request.user
    customer = stripe.Customer.search(query=f"email: '{user.email}'").data[0]
    stripe.Customer.delete(customer.id)
    user.delete()
    return redirect("home")

def catalog(request, query=None):
    categories = None
    price = None
    if query:
        match_categories = re.search(r"categories=([^&]+)", query)
        match_price = re.search(r"price=([^&]+)", query)

        if match_categories:
            categories = [name.replace('$', ' ') for name in match_categories.group(1).split('_')]
        if match_price:
            price = match_price.group(1)
    all_categories = [category.type for category in Category.objects.all()]
    products = Product.objects.all().order_by("?")

    if categories:
        filtered_categories = [category.pk for category in Category.objects.filter(type__in=categories)]
        products = products.filter(category_id__in=filtered_categories)
    if price:
        price_matching = {'price1': (0, 50.99), 'price2': (51, 150.99), 'price3': (151, 500.99), 'price4': (501, 1000.99), 'price5': 1001}
        limit = price_matching[price]
        if price == 'price5':
            products = products.filter(price__gte=limit)
        else:
            products = products.filter(price__range=(limit[0], limit[1]))

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(paginator.num_pages)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    categories = categories if categories else 'null'
    price = price if price else 'null'
    context = {'title': "Catalog", 'current_year': current_year, "user": request.user, 'categories': all_categories,
               'filtered_cat': categories, 'filtered_price': price, 'page_obj': page_obj}
    return render(request, "my_app/catalog/products.html", context=context)

''' API WEBHOOKS '''

# returns order summary (tax, shipping, total, subtotal)
def get_order_summary(request):
    if request.method == "POST":
        try:
            cart = ShoppingCart(request)
            data = json.loads(request.body)
            if type(data['address_id']) == int:
                location = Location.objects.get(pk=data['address_id'])
            else:
                location = data["address_id"]
            products, subtotal = cart.get_shopping_list()
            line_items = [{"amount": round(item['price'] * 100) * item['quantity'],
                           "reference": item["name"]} for item in products]
            result = calculate_tax(line_items, location)

            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON Format"})
    else:
        return JsonResponse({"error": "Invalid request method"})


@login_required
def get_address_from_id(request, _id):
    location = Location.objects.get(pk=_id)
    result = {
        "name": request.user.first_name + " " + request.user.last_name,
        "address": (location.address + " " + location.details).strip(),
        "locale": location.city + ", " + location.state + ", " + location.zipcode + ", " + location.country
    }
    return JsonResponse(result)

@login_required
def get_billing_from_id(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            pm_id = data.get("pm_id")
        except json.JSONDecoder:
            return JsonResponse({"error": "Invalid JSON Format"})
        try:
            payment = stripe.PaymentMethod.retrieve(pm_id)
            billing = payment['billing_details']
            result = {
                "card": f"{payment['type'].replace("_", ' ').title()} ending in {payment[payment['type']]['last4']}",
                'address': f"{billing['address']['line1']} {billing['address']['line2'] if billing['address']['line2'] else ''}",
                'locale': f"{billing['address']['city']}, {billing['address']['state']}, {billing['address']['postal_code']}, {billing['address']['country']}",
                'name': billing['name']
            }
            return JsonResponse(result)
        except stripe.error.InvalidRequestError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except KeyError as e:
            return JsonResponse({"error": f"Missing key in Stripe response: {e}"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def create_express_checkout(request):
    if request.method == "POST":
        try:
            customer = ""
            if request.user.is_authenticated:
                customer = stripe.Customer.search(query=f"email: '{request.user.email}'").data[0]
            data = json.loads(request.body)
            location = Location.objects.get(pk=data.get("addressId"))

            confirmation = stripe.PaymentIntent.create(
                amount = data['total'],
                currency="usd",
                customer=customer["id"] if customer else None,
                payment_method=data["paymentId"],
                receipt_email=request.user.email if request.user.is_authenticated else None,
                shipping= {
                    "address": {
                        "city": location.city,
                        "country": location.country,
                        "line1": location.address,
                        "line2": location.details,
                        "postal_code": location.zipcode,
                        "state": location.state
                    },
                    "name": customer["name"]
                },
                metadata={
                    "tax": data["tax"],
                    "subtotal": data["subtotal"],
                    "shipping": data["shipping"]
                }
            )
            return JsonResponse({"pi_id": confirmation.id})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON Format"})
    else:
        return JsonResponse({"error": "Invalid response method"})

@csrf_protect
def create_payment_intent(request):
    customer = ""
    if request.user.is_authenticated:
        customer = stripe.Customer.search(query=f"email: '{request.user.email}'").data[0]['id']
    cart = ShoppingCart(request)
    products, subtotal = cart.get_shopping_list()
    line_items = [{"amount": round(item['price'] * 100) * item['quantity'],
                   "reference": item["name"]} for item in products]
    result = calculate_tax(line_items)
    payment = stripe.PaymentIntent.create(
        amount=round(result['total'] * 100),
        metadata={
            "tax": int(result["tax"] * 100),
            "subtotal": int(result["subtotal"] * 100),
            "shipping": int(result["shipping"] * 100)
        },
        setup_future_usage = 'on_session',
        customer=customer if customer else None,
        automatic_payment_methods={"enabled": True},
        currency="usd"
    )
    success_link = request.build_absolute_uri(reverse('payment_success', kwargs={"pi_id": payment.id}))
    fail_link = request.build_absolute_uri(reverse("shop_cart"))
    data = {
        "public_key": os.environ.get("STRIPE_PUBLISHABLE_KEY"),
        "client_secret": payment["client_secret"],
        "pi_id": payment["id"],
        "success_link": success_link,
        "fail_link": fail_link
    }

    if customer:
        customer = stripe.Customer.retrieve(customer)
        # Find all billing information
        payment_method = stripe.Customer.list_payment_methods(customer["id"])["data"]
        if payment_method:
            billing_details = payment_method[0]["billing_details"]
            data |= {"billingDetails": billing_details}
        # Find all addresses
        if customer["address"]:
            data |= {"address": customer["address"].to_dict()}
    return JsonResponse(data)

def update_payment_intent(request):
    if request.method == "POST":
        try:
            cart = ShoppingCart(request)
            data = json.loads(request.body)
            pi_id = data.get("pi_id")
            address = data.get("address")
            products, subtotal = cart.get_shopping_list()
            line_items = [{"amount": round(item['price'] * 100) * item['quantity'],
                           "reference": item["name"]} for item in products]
            result = calculate_tax(line_items, address)
            stripe.PaymentIntent.modify(
                pi_id,
                amount=round(result['total'] * 100),
                metadata={
                    "tax": int(result["tax"] * 100),
                    "subtotal": int(result["subtotal"] * 100),
                    "shipping": int(result["shipping"] * 100)
                }
            )
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON Format"})
    else:
        return JsonResponse({"error": "Invalid request method"})

@csrf_protect
def validate_user_delete(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            if authenticate(username=request.user.username, password=data['password']):
                return JsonResponse({"validated": True})
            else:
                return JsonResponse({"validated": False})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"})
    else:
        return JsonResponse({"error": "Invalid request method"})

@csrf_protect
def add_to_cart(request):
    if request.method == "POST":
        try:
            cart = ShoppingCart(request)
            data = json.loads(request.body)
            if cart.add_to_cart(data['name'], 1):
                return JsonResponse({'total': cart.total_items()})
            else:
                return JsonResponse({"error": "Max product amount"})
        except json.JSONDecodeError:
            JsonResponse({"error": "Invalid JSON format"})
    else:
        return JsonResponse({"error": "Invalid request method"})


