import decimal

from django import forms

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Bid(models.Model):
    product_listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name="Bids")
    price = models.DecimalField(max_digits=6, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Bids")


class Listing(models.Model):
    product = models.CharField(max_length=64)
    description = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Listings")
    category = models.CharField(max_length=64, blank=True, default="No Category Listed")
    created = models.DateField()
    starting_price = models.DecimalField(max_digits=6, decimal_places=2, default=decimal.Decimal(0))
    current_price = models.DecimalField(max_digits=6, decimal_places=2, default=decimal.Decimal(0))
    image = models.URLField(max_length=400, blank=True)
    status = models.CharField(max_length=10, default="live")

    def __str__(self):
        return f"{self.product}\nPrice: {self.current_price}\nCreated {self.created}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Comments")
    product = models.ForeignKey(Listing, on_delete=models.CASCADE)
    text = models.CharField(max_length=400)


class Watchlist(models.Model):
    product_listing = models.ForeignKey('Listing', on_delete=models.CASCADE, related_name="Watching")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Watchers")