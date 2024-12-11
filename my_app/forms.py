from django import forms
from django.core.validators import RegexValidator
import datetime
from .countries import country_tuples, country_dict
from .models import Location, User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class RegisterForm(forms.Form):
    first_name = forms.CharField(label="First Name: *", required=True)
    last_name = forms.CharField(label="Last Name: *", required=True)
    username = forms.CharField(label="Username: *", required=True)
    email = forms.EmailField(label="Email Address: *", required=True)
    phone = forms.CharField(
        label="Phone Number: ",
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[1]?[ -]?[(]?\d{3}[)]?[ -]?\d{3}[ -]?\d{4}$",
                message="Format: ###-###-#### or 1 ###-###-####"
            )
        ]
    )
    password = forms.CharField(label="Create Password: *", required=True, widget=forms.PasswordInput, min_length=8)
    confirm = forms.CharField(label="Retype Password: *", required=True, widget=forms.PasswordInput, min_length=8)
    agree = forms.BooleanField(
        label="Do you wish for us to collect personal data for research purposes? (Check the box to sign up for data collection)",
        required=False
    )
    tos = forms.BooleanField(label="Do you agree to our terms of services? *", required=True)
    # Custom clean method to check if passwords match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")

        if password and confirm and password != confirm:
            self.add_error("confirm", "Passwords must match")
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.CharField(label="Email Address / Username: *", required=True)
    password = forms.CharField(label="Enter Password: *", required=True, widget=forms.PasswordInput)


class ResetForm(forms.Form):
    email = forms.CharField(label="Email Address/Username: *", required=True)


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(label="Create New Password: *", required=True, widget=forms.PasswordInput, min_length=8)
    confirm = forms.CharField(label="Retype Password: *", required=True, widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")

        if password and confirm and password != confirm:
            self.add_error("confirm", "Passwords must match")
        return cleaned_data

class DateInput(forms.DateInput):
    input_type = "date"

class EditProfileForm(forms.Form):
    first_name = forms.CharField(label="First Name: *", required=True)
    last_name = forms.CharField(label="Last Name: *", required=True)
    username = forms.CharField(label="Username: *", required=True)
    email = forms.EmailField(label="Email Address: *")
    phone = forms.CharField(
        label="Phone Number: ",
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[1]?[ -]?[(]?\d{3}[)]?[ -]?\d{3}[ -]?\d{4}$",
                message="Format: ###-###-#### or 1 ###-###-####"
            )
        ]
    )

    birth_date = forms.DateField(label="Enter your Birthday", required=False, widget=DateInput())

class LocationForm(forms.Form):
    address = forms.CharField(label="Street Address: *", required=True,
                              widget=forms.TextInput(attrs={"id": "main_address"}))
    details = forms.CharField(label="Apartment, unit, suite, or floor #", required=False,
                              widget=forms.TextInput(attrs={"id": "address_details"}))
    city = forms.CharField(label="City: *", required=True, widget=forms.TextInput(attrs={"id": "city"}))
    state = forms.CharField(label="State / Province: *", required=True, widget=forms.TextInput(attrs={"id": "state"}))
    zipcode = forms.CharField(label="Postal code: *", required=True, widget=forms.TextInput(attrs={"id": "zip_code"}))
    country = forms.ChoiceField(label="Country / Region: *", required=True, choices=[("", "Please Select")] + country_tuples,
                              widget=forms.Select(attrs={"id": "country"}))
    def clean(self):
        cleaned_data = super().clean()
        country_name = cleaned_data.get("country")
        cleaned_data["country"] = country_dict[country_name]

class PaymentLocationForm(LocationForm):
    months = [str(i) if i >= 10 else "0" + str(i) for i in range(1, 13)]
    years = [str(i) for i in range(datetime.datetime.now().year, 2100)]
    month = forms.ChoiceField(label="Month", choices=tuple((m, m) for m in months))
    year = forms.ChoiceField(label="Year", choices=tuple((y, y) for y in years))

class ProductForm(forms.Form):
    name = forms.CharField(label="Name", required=True)
    category = forms.CharField(label='Category', required=True)
    description = forms.CharField(label="Description", required=True)
    price = forms.DecimalField(label="Price", decimal_places=2, max_digits=7, required=True)
    stock = forms.IntegerField(label="Stock", required=True)
    image = forms.ImageField(required=True)
    is_active = forms.BooleanField(label="Activate Product? ", required=False)

class ContactForm(forms.Form):
    name = forms.CharField(label="Your Name", required=True)
    email = forms.EmailField(label="Email Address", required=True)
    subject = forms.CharField(label="Subject", required=True)
    message = forms.CharField(label="Message", widget=forms.Textarea(attrs={"rows": 5}))

class AddCartForm(forms.Form):
    amount = forms.IntegerField(label="Quantity", required=True, initial=1, min_value=1, max_value=100)

class SelectAddressForm(forms.Form):
    locations = forms.ModelChoiceField(queryset=Location.objects.none(), widget=forms.RadioSelect, required=True)


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(SelectAddressForm, self).__init__(*args, **kwargs)
        qs = Location.objects.filter(users=user)
        self.fields["locations"].queryset = qs
        self.fields["locations"].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        street = obj.address + obj.details
        return f"{street.strip()}, {obj.city}, {obj.state}, {obj.zipcode}, {obj.country}"

class CheckoutAddressForm(forms.Form):
    address = forms.CharField(label="Street Address: ", required=True,
                              widget=forms.TextInput(attrs={"id": "main_address"}))
    details = forms.CharField(label="Apartment, unit, suite, or floor #", required=False,
                              widget=forms.TextInput(attrs={"id": "address_details"}))
    city = forms.CharField(label="City: ", required=True, widget=forms.TextInput(attrs={"id": "city"}))
    state = forms.CharField(label="State / Province: ", required=True, widget=forms.TextInput(attrs={"id": "state"}))
    zipcode = forms.CharField(label="Postal code: ", required=True, widget=forms.TextInput(attrs={"id": "zip_code"}))
    country = forms.ChoiceField(label="Country / Region: ", required=True,
                                choices=[("", "Please Select")] + country_tuples,
                                widget=forms.Select(attrs={"id": "country"}))
    def clean(self):
        cleaned_data = super().clean()
        country_name = cleaned_data.get("country")
        cleaned_data["country"] = country_dict[country_name]