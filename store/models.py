from django.db import models
from django.contrib.auth.models import User
import joblib
import pickle
# from .sentiment import  SentimentNetwork
# from .sentiment import load_data

# max_reviews = 5000
# data = load_data("reviews.jsonl", max_reviews)
# if not data:
# 	raise ValueError("No valid data loaded from the JSONL file.")

# print(f"Loaded about {len(data)} reviews.")

# split = int(0.8 * len(data))
# train_data, test_data = data[:split], data[split:]

# train_reviews, train_labels = zip(*train_data)
# test_reviews, test_labels = zip(*test_data)

# network = SentimentNetwork(train_reviews, train_labels, min_count=5, polarity_cutoff=0.05, hidden_nodes=20)
# network.train(train_reviews, train_labels)
# network.test(test_reviews, test_labels)

class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null= True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
	name = models.CharField(max_length=200)
	price = models.FloatField()
	digital = models.BooleanField(default=False,null=True, blank=True)
	image = models.ImageField(null=True, blank=True)
	review = models.CharField(max_length=200, null=True, blank=True)

	def __str__(self):
		return self.name
	
	@property
	def imageURL(self):
		try:
			url = self.image.url
		except:
			url = ''
		return url

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.CharField(max_length=100)
    review = models.TextField()
    sentiment = models.CharField(max_length=200, null=True, blank=True)
    
    # def save(self, *args, **kwargs):
    #     self.sentiment = network.run(self.review)
    #     super(Review, self).save(*args, **kwargs)
    
    # def __str__(self):
    #     return f'Review by {self.user} on {self.product.name}'
      
class Order(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
	date_ordered = models.DateTimeField(auto_now_add=True)
	complete = models.BooleanField(default=False)
	transaction_id = models.CharField(max_length=100, null=True)

	def __str__(self):
		return str(self.id)
	
	@property
	def shipping(self):
		shipping = False
		orderitems = self.orderitem_set.all()
		for i in orderitems:
			if i.product.digital == False:
				shipping = True
		return shipping
	
	@property
	def get_cart_total(self):
		orderitems= self.orderitem_set.all()
		total = sum([item.get_total for item in orderitems])
		return total

	@property
	def get_cart_items(self):
		orderitems = self.orderitem_set.all()
		total = sum([item.quantity for item in orderitems])
		return total

class OrderItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	quantity = models.IntegerField(default=0, null=True, blank=True)
	date_added = models.DateTimeField(auto_now_add=True)

	@property
	def get_total(self):
		total = self.product.price * self.quantity
		return total

class ShippingAddress(models.Model):
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
	order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
	address = models.CharField(max_length=200, null=False)
	city = models.CharField(max_length=200, null=False)
	state = models.CharField(max_length=200, null=False)
	zipcode = models.CharField(max_length=200, null=False)
	date_added = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.address
