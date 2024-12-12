"""
URL configuration for my_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from my_app import views
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', views.home, name='home'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('register/', views.register, name='register'),
    path('login/', views.signin, name='login'),
    path('terms-of-services/', views.tos, name='tos'),
    path('logout/', views.signout, name='logout'),
    path('reset/', views.reset_password, name='reset_password'),
    path('set_password/<uidb64>/<token>', views.set_password, name='set_password'),
    path('profile/', views.profile_account, name='profile'),
    path('profile/locations', views.profile_location, name='locations'),
    path('profile/add_address', views.add_address, name='add_address'),
    path('profile/edit_address/<int:_id>', views.edit_address, name='edit_address'),
    path('profile/delete_address/<int:_id>', views.delete_address, name='delete_address'),
    path('profile/payments', views.profile_payment, name='payments'),
    path('profile/add_payment', views.add_payment, name='add_payment'),
    path('profile/create_setup_intent', views.create_setup_intent, name='create_setup'),
    path('profile/edit_payment/<pm_id>>', views.edit_payment, name='edit_payment'),
    path('profile/delete_payment/<pm_id>>', views.delete_payment, name='delete_payment'),
    path('profile/orders', views.profile_orders, name='orders'),
    path('profile/delete_account', views.delete_account, name='delete_account'),
    path('add_product/', views.add_product, name="add_product"),
    path('edit_product/', views.edit_product, name="edit_product"),
    path('product/<name>', views.product, name='product'),
    path('shop_cart', views.shop_cart, name="shop_cart"),
    path('update_cart/<name>/<int:quantity>', views.update_cart, name="update_cart"),
    path('shop_cart/<name>', views.delete_item, name="delete_item"),
    path('session_checkout', views.session_checkout, name="session_checkout"),
    path('confirm_checkout', views.confirm_checkout, name="confirm_checkout"),
    path('payment_success/<pi_id>', views.payment_success, name="payment_success"),
    path('review_order/<order_num>', views.review_order, name="review_order"),
    path('favicon.ico', RedirectView.as_view(url='static/favicon.ico')),
    path('catalog', views.catalog, name="catalog"),
    path('catalog/<str:query>/', views.catalog, name='catalog_query')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

api_webhooks = [
    path('get_location_from_id/<int:_id>', views.get_address_from_id, name="get_location_from_id"),
    path('get_billing_from_id', views.get_billing_from_id, name="get_billing_from_id"),
    path('get_order_summary', views.get_order_summary, name="get_order_summary"),
    path('create_express_checkout', views.create_express_checkout, name="create_express_checkout"),
    path('finalize_express_checkout/<pi_id>/<email>', views.finalize_express_checkout, name="finalize_express_checkout"),
    path('create_payment_intent', views.create_payment_intent, name="create_payment_intent"),
    path('update_payment_intent', views.update_payment_intent, name="update_payment_intent"),
    path('profile/validate_user_delete', views.validate_user_delete, name="validate_user_delete"),
    path('profile/delete_user_account', views.delete_user_account, name="delete_user_account"),
    path('add_to_cart', views.add_to_cart, name="add_to_cart"),
]

urlpatterns.extend(api_webhooks)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)