import datetime
import decimal

from django import forms

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Bid, Listing, Comment, Watchlist

class NewListingForm(forms.Form):
    product = forms.CharField(max_length=64)
    description = forms.CharField(widget=forms.Textarea)
    category = forms.CharField(max_length=64, required=False)
    starting_price = forms.DecimalField(max_digits=6, decimal_places=2)
    image = forms.URLField(max_length=400, required=False)


def index(request):
    listings = Listing.objects.all()
    return render(request, "auctions/index.html", {
        'listings': listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == "POST":
        # Get current username
        if request.user.is_authenticated:
            username = request.user.username
        
        # If not logged in send to login page
        else:
            return HttpResponseRedirect(reverse("login"))
        
        for user in User.objects.all():
            if username == user.username:
                break

        # Get time
        created = datetime.datetime.now()

        entry_form = NewListingForm(request.POST)

        if entry_form.is_valid():
            product = entry_form.cleaned_data["product"]
            description = entry_form.cleaned_data["description"]
            category = entry_form.cleaned_data["category"]
            starting_price = entry_form.cleaned_data["starting_price"]
            image = entry_form.cleaned_data["image"]

        listing = Listing(product=product, description=description, user=user, category=category, created=created, starting_price=starting_price, current_price=starting_price, image=image)
        listing.save()

        listings = Listing.objects.all()

        return HttpResponseRedirect(reverse("index"))

    else:
        # To make sure user can't acces this page without being logged in
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        
        entry_form = NewListingForm()
        return render(request, "auctions/create_listing.html", {
            'entry_form': entry_form
        })


def listing(request, listing_id):
    if request.method == "GET":
        listings = Listing.objects.all()
        for listing in listings:
            if listing.id == listing_id:
                break

        comments = Comment.objects.filter(product__id__exact=listing_id)
        watchlist = Watchlist.objects.filter(product_listing__id__exact=listing_id).filter(user__username__exact=request.user)
        if len(watchlist) == 0:
            watch = 0
        else:
            watch = 1

        if listing.status == "ended":
            bids = Bid.objects.filter(product_listing__product__exact=listing.product)
            highest_bid = max(bids, key=lambda bids:bids.price)
            highest_bidder = highest_bid.user.username

            return render(request, "auctions/listing.html", {
                "listing": listing,
                "highest_bidder": highest_bidder,
                "comments": comments,
                "watch": watch
            })

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "comments": comments,
            "watch": watch
        })

    else:
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))

        comments = Comment.objects.filter(product__id__exact=listing_id)
        user = User.objects.filter(username__exact=request.user)[0]
        watchlist = Watchlist.objects.filter(product_listing__id__exact=listing_id).filter(user__username__exact=request.user)
        if len(watchlist) == 0:
            watch = 0
        else:
            watch = 1

        listings = Listing.objects.all()
        for listing in listings:
            if listing.id == listing_id:
                break

        # Add or remove to or from watchlist
        if request.POST.get("add_watch") is not None:
           
            watch = Watchlist(product_listing=listing, user=user)
            watch.save()
            watchlist = Watchlist.objects.filter(user__exact=user).filter(product_listing__exact=listing)
            if len(watchlist) == 0:
                watch = 0
            else:
                watch = 1

            return render(request, "auctions/listing.html", {
                "listing": listing,
                "comments": comments,
                "watch": watch
            })
        
        if request.POST.get("remove_watch") is not None:
            watch = Watchlist.objects.filter(user__exact=user).filter(product_listing__exact=listing)
            watch.delete()

            watchlist = Watchlist.objects.filter(user__exact=user).filter(product_listing__exact=listing)
            if len(watchlist) == 0:
                watch = 0
            else:
                watch = 1

            return render(request, "auctions/listing.html", {
            "listing": listing,
            "comments": comments,
            "watch": watch
            })
        
        # Close auction on button click
        if request.POST.get("close_auction") is not None:
            product = listing.product
            bids = Bid.objects.filter(product_listing__product__exact=product)
            highest_bid = max(bids, key=lambda bids:bids.price)
            highest_bidder = highest_bid.user.username

            listing.status = "ended"
            listing.save()

            return render(request, "auctions/listing.html", {
                "listing": listing,
                "highest_bidder": highest_bidder,
                "comments": comments,
                "watch": watch
            })
        
        # Add comment
        if request.POST.get("comment") is not None:
            text = request.POST.get("comment")
            username = request.user.username
            user = User.objects.filter(username__exact=username)[0]
            product_id = request.path.split('/')[-1]
            listing = Listing.objects.filter(id__exact=product_id)[0]

            new_comment = Comment(user=user, product=listing, text=text)
            new_comment.save()

            comments = Comment.objects.filter(product__id__exact=listing_id)

            return render(request, "auctions/listing.html", {
                "listing": listing,
                "comments": comments,
                "watch": watch
            })
        
        # Get bid from form
        bid = decimal.Decimal(request.POST.get("bid"))

        # Make sure its larger than the current price
        if bid <= listing.current_price:
            messages.add_message(request, messages.ERROR, "Bid too small!")
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "comments": comments,
                "watch": watch
            })
        
        # Get the logged in user
        username = request.user.username
        for user in User.objects.all():
            if username == user.username:
                break

        # Save the bid in the model
        new_bid = Bid(product_listing=listing, price=bid, user=user)
        new_bid.save()

        # Update the current price for this product
        listing.current_price = bid
        listing.save()

        return render(request, "auctions/listing.html", {
            "listing": listing,
            "comments": comments,
            "watch": watch
        })

def watchlist(request, user_id):
    user = User.objects.filter(username__exact=user_id)[0]
    user_watchlist = Watchlist.objects.filter(user__exact=user)

    user_list = []
    for watch in user_watchlist:
        user_list.append(watch.product_listing)

    return render(request, "auctions/index.html", {
        "listings": user_list
    })

