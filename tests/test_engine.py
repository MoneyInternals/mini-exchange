"""Spec for the MatchingEngine. Make these pass by implementing
src/exchange/engine.py (the book must already work).

Run:  pytest tests/test_engine.py

These encode every rule you need: crossing, partial fills, price-time priority,
price improvement, market-order sweeps, and what happens with no liquidity.
"""
from exchange.domain import Order, OrderType, Side
from exchange.engine import MatchingEngine


def limit(id_, side, price, qty):
    return Order(id=id_, side=side, type=OrderType.LIMIT, quantity=qty, price=price)


def market(id_, side, qty):
    return Order(id=id_, side=side, type=OrderType.MARKET, quantity=qty)


def test_resting_limit_makes_no_trade():
    eng = MatchingEngine()
    trades = eng.submit(limit("a1", Side.SELL, 101.0, 10))
    assert trades == []
    assert eng.book.best_ask() == 101.0


def test_full_cross_produces_one_trade():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 10))
    trades = eng.submit(limit("b1", Side.BUY, 100.0, 10))
    assert len(trades) == 1
    t = trades[0]
    assert t.price == 100.0
    assert t.quantity == 10
    assert t.maker_order_id == "a1"
    assert t.taker_order_id == "b1"
    assert eng.book.best_ask() is None
    assert eng.book.best_bid() is None


def test_incoming_larger_rests_the_remainder():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 5))
    trades = eng.submit(limit("b1", Side.BUY, 100.0, 8))
    assert sum(t.quantity for t in trades) == 5
    # 3 of the buy is left and now rests as the best bid
    assert eng.book.best_bid() == 100.0
    resting = eng.book.orders_at(Side.BUY, 100.0)
    assert len(resting) == 1 and resting[0].remaining == 3


def test_resting_larger_keeps_remainder_on_book():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 10))
    trades = eng.submit(limit("b1", Side.BUY, 100.0, 4))
    assert sum(t.quantity for t in trades) == 4
    assert eng.book.best_ask() == 100.0
    resting = eng.book.orders_at(Side.SELL, 100.0)
    assert len(resting) == 1 and resting[0].remaining == 6


def test_price_time_priority_oldest_fills_first():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 5))  # arrived first
    eng.submit(limit("a2", Side.SELL, 100.0, 5))  # arrived second, same price
    trades = eng.submit(limit("b1", Side.BUY, 100.0, 5))
    assert len(trades) == 1
    assert trades[0].maker_order_id == "a1"        # oldest wins
    resting = eng.book.orders_at(Side.SELL, 100.0)
    assert len(resting) == 1 and resting[0].id == "a2" and resting[0].remaining == 5


def test_taker_gets_price_improvement():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 5))
    trades = eng.submit(limit("b1", Side.BUY, 105.0, 5))  # willing to pay up to 105
    assert len(trades) == 1
    assert trades[0].price == 100.0      # fills at the maker's price, not 105
    assert eng.book.best_bid() is None   # buy fully filled, nothing rests


def test_market_order_sweeps_multiple_levels():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 3))
    eng.submit(limit("a2", Side.SELL, 101.0, 3))
    eng.submit(limit("a3", Side.SELL, 102.0, 3))
    trades = eng.submit(market("m1", Side.BUY, 7))
    assert [(t.price, t.quantity) for t in trades] == [(100.0, 3), (101.0, 3), (102.0, 1)]
    assert sum(t.quantity for t in trades) == 7
    resting = eng.book.orders_at(Side.SELL, 102.0)
    assert len(resting) == 1 and resting[0].remaining == 2


def test_market_order_without_liquidity_does_not_rest():
    eng = MatchingEngine()
    trades = eng.submit(market("m1", Side.BUY, 5))
    assert trades == []
    assert eng.book.best_bid() is None
    assert eng.book.best_ask() is None


def test_cancel_then_no_match():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 5))
    eng.cancel("a1")
    trades = eng.submit(limit("b1", Side.BUY, 100.0, 5))
    assert trades == []
    assert eng.book.best_bid() == 100.0  # the buy rests; nothing left to match
