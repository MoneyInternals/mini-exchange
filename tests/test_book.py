"""Spec for the OrderBook. Make these pass by implementing src/exchange/book.py.

Run:  pytest tests/test_book.py
Tackle them roughly top-to-bottom — each builds on the last.
"""
from exchange.book import OrderBook
from exchange.domain import Order, OrderType, Side


def limit(id_, side, price, qty):
    return Order(id=id_, side=side, type=OrderType.LIMIT, quantity=qty, price=price)


def test_empty_book_has_no_best_prices():
    book = OrderBook()
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_add_sets_best_ask():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 101.0, 5))
    assert book.best_ask() == 101.0
    assert book.best_bid() is None


def test_best_bid_is_highest_price():
    book = OrderBook()
    book.add(limit("b1", Side.BUY, 100.0, 5))
    book.add(limit("b2", Side.BUY, 102.0, 5))
    book.add(limit("b3", Side.BUY, 99.0, 5))
    assert book.best_bid() == 102.0


def test_best_ask_is_lowest_price():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 105.0, 5))
    book.add(limit("a2", Side.SELL, 103.0, 5))
    book.add(limit("a3", Side.SELL, 108.0, 5))
    assert book.best_ask() == 103.0


def test_orders_at_a_level_are_fifo():
    book = OrderBook()
    book.add(limit("o1", Side.BUY, 100.0, 5))
    book.add(limit("o2", Side.BUY, 100.0, 7))
    queue = book.orders_at(Side.BUY, 100.0)
    assert [o.id for o in queue] == ["o1", "o2"]  # oldest first


def test_cancel_removes_liquidity():
    book = OrderBook()
    book.add(limit("b1", Side.BUY, 100.0, 5))
    removed = book.cancel("b1")
    assert removed is not None and removed.id == "b1"
    assert book.best_bid() is None
    assert book.orders_at(Side.BUY, 100.0) == []


def test_cancel_unknown_order_returns_none():
    book = OrderBook()
    assert book.cancel("does-not-exist") is None
