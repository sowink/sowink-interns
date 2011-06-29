from django import forms
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404

from mall.models import Gift, UserGift


MSG_BALANCE_LOW = (u'User does not have enough balance to purchase gift')


def deduct_balance(creator, gift, bought_with):
    """Deducts creator's balance from purchasing a gift.

    Assumes creator has enough balance by a preliminary check performed before
    calling deduct_balance().

    """
    profile = creator.profile
    if bought_with == 1:
        profile.update(winkcash=profile.winkcash - gift.winkcash)
    else:
        profile.update(coins=profile.coins - gift.coins)
    

class BuyGiftForm(forms.ModelForm):
    """Form to buy a gift."""
    def __init__(self, bought_with, data=None, 
                 *args, **kwargs): 
        if data:
            data = data.copy()
            data['bought_with'] = bought_with
        super(BuyGiftForm, self).__init__(data=data, *args, **kwargs)


    def clean(self):
        """Determine whether creator has enough balance to make purchase"""

        cleaned_data = self.cleaned_data
        gift = cleaned_data.get("gift")
        creator = cleaned_data.get("creator")
        bought_with = cleaned_data.get("bought_with")

        # Determine which balance to check, winkcash or coins.
        if bought_with == 1:
            user_balance = creator.profile.winkcash
            gift_cost = gift.winkcash
        else:
            user_balance = creator.profile.coins
            gift_cost = gift.coins
        
        # Check creator's balance.
        if gift_cost > user_balance:
            raise forms.ValidationError(MSG_BALANCE_LOW)
        else:
            deduct_balance(creator, gift, bought_with)

        return cleaned_data


    class Meta:
        model = UserGift
        exclude = ['created']
