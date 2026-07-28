"""Spec for episode 3 — price-time priority made observable.

The matching behaviour already works (test_engine.py). This file specs the two
things the UI needs and the engine currently cannot answer:

  1. QUEUE INTROSPECTION — where am I in the queue, and how much is ahead of me?
  2. STATUS LIFECYCLE    — an order that has been partly eaten should say so.

Run:  pytest tests/test_priority.py
"""
from exchange.domain import Order, OrderStatus, OrderType, Side
from exchange.engine import MatchingEngine


def limit(id_, side, price, qty):
    return Order(id=id_, side=side, type=OrderType.LIMIT, quantity=qty, price=price)


def market(id_, side, qty):
    return Order(id=id_, side=side, type=OrderType.MARKET, quantity=qty)


def three_deep():
    """a1(10), a2(8), you(10) all resting at 100.00, in that arrival order."""
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 10))
    eng.submit(limit("a2", Side.SELL, 100.0, 8))
    eng.submit(limit("you", Side.SELL, 100.0, 10))
    return eng


# --- front_at: the helper the engine matches against ----------------------

def test_front_at_returns_the_oldest_order():
    eng = three_deep()
    assert eng.book.front_at(Side.SELL, 100.0).id == "a1"


def test_front_at_returns_none_for_an_empty_level():
    eng = MatchingEngine()
    assert eng.book.front_at(Side.SELL, 100.0) is None


# --- queue position -------------------------------------------------------

def test_queue_position_is_arrival_order():
    eng = three_deep()
    assert eng.book.queue_position("a1") == 1
    assert eng.book.queue_position("a2") == 2
    assert eng.book.queue_position("you") == 3


def test_queue_position_is_none_for_an_order_not_on_the_book():
    eng = three_deep()
    assert eng.book.queue_position("nope") is None


def test_queue_position_only_counts_the_same_price_level():
    eng = three_deep()
    eng.submit(limit("higher", Side.SELL, 101.0, 5))
    # a fresh level, so it is first in its own queue — not fourth overall
    assert eng.book.queue_position("higher") == 1


# --- units ahead: the number that decides whether you fill ---------------

def test_units_ahead_sums_the_orders_in_front():
    eng = three_deep()
    assert eng.book.units_ahead("a1") == 0
    assert eng.book.units_ahead("a2") == 10
    assert eng.book.units_ahead("you") == 18


def test_units_ahead_counts_remaining_not_original_quantity():
    """The subtle one. A half-eaten order ahead of you only blocks what is LEFT
    of it. Sum `quantity` here and the number is wrong the moment anyone trades."""
    eng = three_deep()
    eng.submit(market("m1", Side.BUY, 12))   # takes all of a1, then 2 of a2
    assert eng.book.units_ahead("you") == 6  # a2 has 6 left — not 8, not 18


# --- status lifecycle -----------------------------------------------------

def test_a_resting_order_is_open():
    eng = three_deep()
    assert eng.book.front_at(Side.SELL, 100.0).status is OrderStatus.OPEN


def test_partial_fill_marks_the_maker_partially_filled():
    eng = three_deep()
    eng.submit(market("m1", Side.BUY, 12))
    a2 = eng.book.front_at(Side.SELL, 100.0)
    assert a2.id == "a2"
    assert a2.remaining == 6
    assert a2.status is OrderStatus.PARTIALLY_FILLED


def test_partial_fill_marks_the_taker_too():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 4))
    taker = limit("b1", Side.BUY, 100.0, 10)
    eng.submit(taker)                        # fills 4, rests 6
    assert taker.remaining == 6
    assert taker.status is OrderStatus.PARTIALLY_FILLED


def test_a_fully_consumed_maker_is_filled_not_cancelled():
    """The trap: the engine removes a spent maker via the book. If removal is what
    sets the status, a filled order ends up marked CANCELLED and the tape lies."""
    eng = MatchingEngine()
    maker = limit("a1", Side.SELL, 100.0, 5)
    eng.submit(maker)
    eng.submit(market("m1", Side.BUY, 5))
    assert maker.remaining == 0
    assert maker.status is OrderStatus.FILLED


def test_cancelling_marks_cancelled():
    eng = three_deep()
    cancelled = eng.cancel("a2")
    assert cancelled.status is OrderStatus.CANCELLED
    assert eng.book.queue_position("a2") is None
    assert eng.book.queue_position("you") == 2   # you move up when they leave


# --- the payoff: priority is earned, and instantly lost ------------------

def test_cancelling_and_re_entering_sends_you_to_the_back():
    eng = MatchingEngine()
    eng.submit(limit("a1", Side.SELL, 100.0, 5))
    eng.submit(limit("you", Side.SELL, 100.0, 5))
    eng.submit(limit("d1", Side.SELL, 100.0, 5))   # arrived after you
    assert eng.book.queue_position("you") == 2

    eng.cancel("you")
    eng.submit(limit("you2", Side.SELL, 100.0, 5))  # same price, same size
    assert eng.book.queue_position("you2") == 3     # behind d1 now
    assert eng.book.units_ahead("you2") == 10


def test_a_newcomer_never_jumps_the_queue():
    eng = three_deep()
    eng.submit(limit("d1", Side.SELL, 100.0, 99))   # huge, but late
    assert eng.book.queue_position("d1") == 4
    assert eng.book.units_ahead("you") == 18        # unchanged by the newcomer
