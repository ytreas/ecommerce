from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import logout
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Review

def store(request):

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = { 'get_cart_items': 0, 'get_cart_total': 0, 'shipping':False}
        cartItems = order['get_cart_items']

    products = Product.objects.all()
    context = {'products': products,'cartItems': cartItems}
    return render(request, 'store/store.html', context)

def cart(request):

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = { 'get_cart_items': 0, 'get_cart_total': 0, 'shipping':False}
        cartItems = order['get_cart_items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer,complete = False)
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        items = []
        order = { 'get_cart_items': 0, 'get_cart_total': 0, 'shipping':False}
        cartItems = order['get_cart_items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        pass

    is_demo_payment = data.get('demoPayment', False)

    if is_demo_payment:
        order.complete = True
    else:
        total = float(data['form']['total'])
        order.transaction_id = transaction_id

        if total == order.get_cart_total:
            order.complete = True
        order.save()

        if order.shipping:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zipcode'],
            )

    if order.complete:
        order.orderitem_set.all().delete()

    return JsonResponse('Payment submitted..', safe=False)


class CustomLoginView(auth_views.LoginView):
    template_name = 'store/login.html'


class CustomLogoutView(View):
    def dispatch(self, request, *args, **kwargs):
        logout(request)
        next_page = self.get_next_page()
        return redirect(next_page)

    def get_next_page(self):
        """
        Get the next page to redirect to after logout.
        Override this method to customize the logout redirect behavior.
        """
        return reverse_lazy('store') 

# Signup view
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.create(user=user)
            return redirect('login')  
    else:
        form = UserCreationForm()
    return render(request, 'store/signup.html', {'form': form})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()
    context = {
        'product': product,
        'reviews': reviews
    }
    return render(request, 'store/product_detail.html', context)

def success_page(request):
    return render(request, 'store/success.html')

def add_review(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        review_text = request.POST['review']
        user = request.user.username 
        Review.objects.create(product=product, user=user, review=review_text)
        return redirect('product_detail', pk=pk)
    
@csrf_exempt
def clear_cart(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            order.orderitem_set.all().delete()
            order.delete()
            return JsonResponse({'message': 'Cart cleared'}, status=200)
        else:
            return JsonResponse({'message': 'User not authenticated'}, status=401)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)