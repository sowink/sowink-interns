def deduct_balance(creator, gift, bought_with):
    """Deducts creator's balance from purchasing a gift.

    Will make appropriate checks to ensure which balance to check and deduct. 
    Returns a boolean value: True if creator has enough balance, otherwise 
    return False.

    """
    profile = creator.profile
    
    # Determine which balance to check, winkcash or coins.
    if bought_with == 1:
        user_balance = creator.profile.winkcash
        gift_cost = gift.winkcash
    else:
        user_balance = creator.profile.coins
        gift_cost = gift.coins
        
    # Check creator's balance.
    if gift_cost > user_balance:
        return False
    else:
        # Deduct creator's balance.
        if bought_with == 1:
            profile.update(winkcash=profile.winkcash - gift.winkcash)
        else:
            profile.update(coins=profile.coins - gift.coins)
    
    return True
