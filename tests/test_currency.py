import pytest
from app.utils.currency import convert_currency, get_exchange_rate
from datetime import datetime

def test_currency_conversion_eur_to_usd():
    amount = 100.00
    from_currency = 'EUR'
    to_currency = 'USD'
    date = datetime.now()
    
    result = convert_currency(amount, from_currency, to_currency, date)
    assert result is not None
    assert isinstance(result, float)
    assert result > 0

def test_currency_conversion_same_currency():
    amount = 100.00
    currency = 'EUR'
    date = datetime.now()
    
    result = convert_currency(amount, currency, currency, date)
    assert result == amount

def test_exchange_rate_retrieval():
    from_currency = 'EUR'
    to_currency = 'USD'
    date = datetime.now()
    
    rate = get_exchange_rate(from_currency, to_currency, date)
    assert rate is not None
    assert isinstance(rate, float)
    assert rate > 0

def test_unsupported_currency():
    amount = 100.00
    from_currency = 'EUR'
    to_currency = 'XYZ'  # Unsupported currency
    date = datetime.now()
    
    with pytest.raises(ValueError):
        convert_currency(amount, from_currency, to_currency, date) 