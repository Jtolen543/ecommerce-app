from .models import Product


class ShoppingCart:
    def __init__(self, request):
        self.request = request
        self.session = request.session

    def list_items(self, name=None):
        if not self.session.get("items"):
            self.session["items"] = []
        temp = self.session["items"]
        temp = set(temp)
        if name: temp.add(name)
        self.session["items"] = list(temp)

    def get_item(self, name):
        if not self.session.get(name):
            return None
        return {name: self.session.get(name)}
    def total_items(self):
        total = 0
        for item in self.session['items']:
            total += int(self.session[item])
        self.session['total'] = total
        return total

    def add_to_cart(self, name, quantity):
        if not self.session.get(name):
            self.session[name] = quantity
        else:
            product = Product.objects.get(name=name)
            number = int(self.session[name])
            if quantity + number > product.stock:
                return False
            else:
                self.session[name] = quantity + number
        self.list_items(name)
        self.total_items()
        return True

    def update_cart(self, name, quantity):
        self.session[name] = quantity
        self.list_items(name)
        self.total_items()

    def delete_item(self, name):
        del self.session[name]
        temp = self.session['items']
        temp.remove(name)
        self.session['items'] = temp
        self.total_items()

    def clear_cart(self):
        if self.session.get("total") == 0:
            return
        for key in self.session["items"]:
            del self.session[key]
        del self.session["items"]
        self.session['total'] = 0

    def get_shopping_list(self):
        keys = [key for key in self.session.get("items", [])]
        products = []
        subtotal = 0

        for key in keys:
            product = Product.objects.get(name=key)
            new_dict = {
                "image": product.image,
                "name": product.name,
                "description": product.description,
                "quantity": int(self.session[key]),
                "price": product.price,
                "stock": product.stock,
            }
            subtotal += new_dict['price'] * new_dict['quantity']
            products.append(new_dict)
        return products, subtotal
