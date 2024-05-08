import django
from django.contrib.auth.models import User
from store.models import (
    Address,
    Cart,
    Category,
    Order,
    Product,
    Size,
    Color,
    ProductImage,
)
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, AddressForm
from django.contrib import messages
from django.views import View
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator  # for Class Based Views
from django.http import HttpResponseForbidden

# Create your views here.


def home(request):
    categories = Category.objects.filter(is_active=True, is_featured=True)[:3]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    context = {
        "categories": categories,
        "products": products,
    }
    return render(request, "store/index.html", context)


def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(id=product.id).filter(
        is_active=True, category=product.category
    )
    context = {
        "product": product,
        "related_products": related_products,
    }
    return render(request, "store/detail.html", context)


def all_categories(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, "store/categories.html", {"categories": categories})


def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        "category": category,
        "products": products,
        "categories": categories,
    }
    return render(request, "store/category_products.html", context)


def get_product(request, slug):
    try:
        product = Product.objects.get(slug=slug)
        context = {"product": product}
        if request.GET.get("size"):
            size = request.GET.get("size")
            context["selected_size"] = size
            print(size)
        return render(request, "product/product.html", context)
    except Exception as e:
        print(e)


# Authentication Starts Here


class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, "account/register.html", {"form": form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, "Congratulations! Registration Successful!")
            form.save()
        return render(request, "account/register.html", {"form": form})


@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    return render(
        request, "account/profile.html", {"addresses": addresses, "orders": orders}
    )


@method_decorator(login_required, name="dispatch")
class AddressView(View):
    def get(self, request):
        form = AddressForm()
        return render(request, "account/add_address.html", {"form": form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            user = request.user
            locality = form.cleaned_data["locality"]
            city = form.cleaned_data["city"]
            state = form.cleaned_data["state"]
            reg = Address(user=user, locality=locality, city=city, state=state)
            reg.save()
            messages.success(request, "New Address Added Successfully.")
        return redirect("store:profile")


@login_required
def remove_address(request, pid):
    a = get_object_or_404(Address, user=request.user, id=pid)
    a.delete()
    messages.success(request, "Address removed.")
    return redirect("store:profile")


@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get("prod_id")
    product = get_object_or_404(Product, id=product_id)


    size_id = request.GET.get("selected_size")
    color_id = request.GET.get("selected_color")
    quantity = request.GET.get("quantity")
  
    print(f"Adding to cart - Product ID: {product_id}, Size: {size_id}, Color: {color_id}, Quantity: {quantity}")

    if item := Cart.objects.filter(product=product, user=user).first():
        if quantity and quantity.isdigit(): 
            item.quantity += int(quantity)
        else:
           
            item.quantity += 1

        item.product_size = size_id or "Medium"
        item.product_color = color_id or "Black"
        item.save()
    else:
        Cart.objects.create(
            user=user,
            product=product,
            product_size=size_id or "Medium",
            product_color=color_id or "Black",
            quantity=int(quantity) if quantity and quantity.isdigit() else 1,
        )
    return redirect("store:cart")

@login_required
def cart(request):
    user = request.user
    cart_products = Cart.objects.filter(user=user)

  
    amount = decimal.Decimal(0)
    shipping_amount = decimal.Decimal(10)
    if cp := [p for p in Cart.objects.all() if p.user == user]:
        for p in cp:
            temp_amount = p.quantity * p.product.price
            amount += temp_amount

  
    addresses = Address.objects.filter(user=user)
   
    print(f"Cart products - User: {user}, Cart: {cart_products}, Amount: {amount}")

    context = {
        "cart_products": cart_products,
        "amount": amount,
        "shipping_amount": shipping_amount,
        "total_amount": amount + shipping_amount,
        "addresses": addresses,
    }
    return render(request, "store/cart.html", context)


@login_required
def remove_cart(request, cart_id):
    if request.method == "GET":
        c = get_object_or_404(Cart, id=cart_id)
        c.delete()
        messages.success(request, "Product removed from Cart.")
    return redirect("store:cart")


@login_required
def plus_cart(request, cart_id):
    if request.method == "GET":
        cp = get_object_or_404(Cart, id=cart_id)
        cp.quantity += 1
        cp.save()
    return redirect("store:cart")


@login_required
def minus_cart(request, cart_id):
    if request.method == "GET":
        cp = get_object_or_404(Cart, id=cart_id)
        # Remove the Product if the quantity is already 1
        if cp.quantity == 1:
            cp.delete()
        else:
            cp.quantity -= 1
            cp.save()
    return redirect("store:cart")


@login_required
def checkout(request):
    if request.method == 'POST':
        user = request.user
        address_id = request.POST.get("address")
        print(f"Checkout - User: {user}, Address ID: {address_id}")
        address = get_object_or_404(Address, id=address_id)

        cart = Cart.objects.filter(user=user)

        for item in cart:
            size_title = item.product_size
            print(f"Size Title: {size_title}")
            color_title = item.product_color
            print(f"Color Title: {color_title}")
            
            try:
                color = Color.objects.get(title=color_title)
                size = Size.objects.get(title=size_title)
                
            except Color.DoesNotExist as e: 
                print(f"Color with title '{color_title}' does not exist in the database.")
               
                color = None
                size = None
                
            Order.objects.create(
                user=user,
                address=address,
                product=item.product,
                quantity=item.quantity,
                size=size,
                color=color,
            )
        cart.delete()
        return redirect("store:orders")
    else:
        return HttpResponseForbidden("Invalid request method")


@login_required
def orders(request):
    all_orders = Order.objects.filter(user=request.user).order_by("-ordered_date")
    return render(request, "store/orders.html", {"orders": all_orders})


def cancel_order(request, order_id):  # sourcery skip: hoist-statement-from-if
    order = get_object_or_404(Order, id=order_id)
    if order.user == request.user:
        # Update the status of the order to "Cancelled"
        order.status = "Cancelled"
        order.save()
    # Perform any other necessary actions for order cancellation

    # Redirect back to the orders page
    return redirect("store:orders")


def shop(request):
    return render(request, "store/shop.html")


def test(request):
    return render(request, "store/test.html")
