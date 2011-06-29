from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.http import Http404
from django.shortcuts import get_object_or_404

from mall.models import Gift
from mall.models import UserGift


# Deducts creator's balance from purchasing gift. Assumes creator has enough balance.
def deduct_balance(creator, gift, bought_with):
    profile = creator.profile
    if bought_with == 1:
        profile.wink_cash = profile.wink_cash - gift.winkcash
    else:
        profile.coins = profile.coins - gift.coins
    profile.save()
    

class BuyGiftForm(forms.ModelForm):
                
    def __init__(self, recipient, bought_with, data=None, 
                 *args, **kwargs): 
        if data:
            data = data.copy()
            data['recipient']= recipient
            data['bought_with'] = bought_with
        super(BuyGiftForm, self).__init__(data=data, *args, **kwargs)


    def clean(self):
        """ Check whether creator has enought balance to make purchase
        
        """

        cleaned_data = self.cleaned_data
        gift = cleaned_data.get("gift")
        creator = cleaned_data.get("creator")
        bought_with = cleaned_data.get("bought_with")

        user_balance = 0
        gift_cost = 0

        if bought_with == 1:
            user_balance = creator.profile.wink_cash
            gift_cost = gift.winkcash
        elif bought_with == 2:
            user_balance = creator.profile.coins
            gift_cost = gift.coins
        
        # Check whether user has enough balance to purchase the gift
        if gift_cost > user_balance:
            raise forms.ValidationError("User does not have enough balance to purchase gift")
        else:
            deduct_balance(creator, gift, bought_with)

        return cleaned_data


    class Meta:
        model = UserGift
        exclude = ('created')
