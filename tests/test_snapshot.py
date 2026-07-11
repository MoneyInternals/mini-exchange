"""Spec for OrderBook.snapshot(). Make these pass by adding a snapshot()
method to src/exchange/book.py.

Run:  pytest tests/test_snapshot.py

snapshot() is the one call the frontend makes: the whole book in one shape.
Per side it must AGGREGATE (sum remaining at each price), COUNT (orders at
each price), and SORT (asks ascending, bids descending — best first on both).
"""
from exchange.book import OrderBook
from exchange.domain import Order, OrderType, Side


def limit(id_, side, price, qty):
    return Order(id=id_, side=side, type=OrderType.LIMIT, quantity=qty, price=price)


def test_empty_book_snapshot():
    book = OrderBook()
    s = book.snapshot()
    assert s["bids"] == []
    assert s["asks"] == []
    assert s["best_bid"] is None
    assert s["best_ask"] is None
    assert s["spread"] is None
    assert s["mid"] is None


def test_single_level_each_side():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 101.0, 5))
    book.add(limit("b1", Side.BUY, 100.0, 10))
    s = book.snapshot()
    assert s["asks"] == [{"price": 101.0, "size": 5, "count": 1}]
    assert s["bids"] == [{"price": 100.0, "size": 10, "count": 1}]
    assert s["best_ask"] == 101.0
    assert s["best_bid"] == 100.0
    assert s["spread"] == 1.0
    assert s["mid"] == 100.5


def test_levels_aggregate_size_and_count():
    book = OrderBook()
    book.add(limit("b1", Side.BUY, 100.0, 10))
    book.add(limit("b2", Side.BUY, 100.0, 7))
    s = book.snapshot()
    assert s["bids"] == [{"price": 100.0, "size": 17, "count": 2}]


def test_asks_sorted_ascending_best_first():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 105.0, 5))
    book.add(limit("a2", Side.SELL, 101.0, 5))
    book.add(limit("a3", Side.SELL, 103.0, 5))
    s = book.snapshot()
    assert [lvl["price"] for lvl in s["asks"]] == [101.0, 103.0, 105.0]
    assert s["best_ask"] == 101.0


def test_bids_sorted_descending_best_first():
    book = OrderBook()
    book.add(limit("b1", Side.BUY, 99.0, 5))
    book.add(limit("b2", Side.BUY, 102.0, 5))
    book.add(limit("b3", Side.BUY, 100.0, 5))
    s = book.snapshot()
    assert [lvl["price"] for lvl in s["bids"]] == [102.0, 100.0, 99.0]
    assert s["best_bid"] == 102.0


def test_one_sided_book_has_no_spread_or_mid():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 101.0, 5))
    s = book.snapshot()
    assert s["best_ask"] == 101.0
    assert s["best_bid"] is None
    assert s["spread"] is None
    assert s["mid"] is None


def test_size_uses_remaining_not_quantity():
    # Once the engine partially fills an order, the ladder must show what's
    # LEFT, not what was originally asked for.
    book = OrderBook()
    o = limit("b1", Side.BUY, 100.0, 10)
    book.add(o)
    o.remaining = 4  # simulate a partial fill (the engine will do this in ep2)
    s = book.snapshot()
    assert s["bids"] == [{"price": 100.0, "size": 4, "count": 1}]


def test_cancel_updates_snapshot():
    book = OrderBook()
    book.add(limit("a1", Side.SELL, 101.0, 5))
    book.add(limit("a2", Side.SELL, 101.5, 8))
    book.cancel("a1")
    s = book.snapshot()
    assert s["best_ask"] == 101.5
    assert [lvl["price"] for lvl in s["asks"]] == [101.5]
