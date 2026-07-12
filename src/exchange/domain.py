"""Domain model — the shared vocabulary the whole system codes against.

This file is GIVEN to you on purpose: it's the contract, not the logic. The
interesting work lives in book.py and engine.py. You're free to extend these
types (add fields, validation, an OrderStatus transition helper), but the tests
assume the names below exist.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """A single order.

    `remaining` tracks how much is still unfilled; it starts equal to `quantity`
    and the engine decrements it as the order trades. `price` is None for MARKET
    orders (they take whatever price the book offers).

    NOTE — a real design decision waits for you here: `price` is a float for now,
    which is fine for this simulator's clean tick values. For real money you'd
    reach for Decimal or integer ticks to avoid float-equality bugs. See README.
    """
    id: str
    side: Side
    type: OrderType
    quantity: int
    price: float | None = None
    remaining: int = field(init=False)          # not Optional, not a constructor arg
    status: OrderStatus = OrderStatus.OPEN

    def __post_init__(self) -> None:
        self.remaining = self.quantity


@dataclass
class Trade:
    """A match between an incoming (taker) order and a resting (maker) order.

    The trade always executes at the MAKER's price — the passive order that was
    already on the book sets the price. That's why a buyer willing to pay 105 can
    fill at a resting ask of 100 ("price improvement").
    """
    price: float
    quantity: int
    taker_order_id: str
    maker_order_id: str
    aggressor: Side
