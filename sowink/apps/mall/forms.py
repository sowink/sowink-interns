from django import forms

from mall.models import UserGift
from mall.utils import deduct_balance

MSG_BALANCE_LOW = u'User does not have enough balance to purchase gift'


class BuyGiftForm(forms.ModelForm):
    """Form to buy a gift."""
    def __init__(self, bought_with=None, data=None,
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

        if not deduct_balance(creator, gift, bought_with):
            raise forms.ValidationError(MSG_BALANCE_LOW)

        return cleaned_data

    class Meta:
        model = UserGift
        exclude = ['created']
