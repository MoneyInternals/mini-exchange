"""OrderBook — YOUR code goes here.

The book is the *data structure*: it stores resting (unmatched) limit orders and
gives fast access to the best prices. It does NOT decide how trades happen — that
is the MatchingEngine's job (engine.py).

Picture two price ladders:
    asks (sellers):  best = LOWEST price
    bids (buyers):   best = HIGHEST price
At each price level, orders queue first-in-first-out — earlier arrivals have
higher time priority.

The order book — implemented in episode 1. Want to build it yourself? Delete the method bodies and
let tests/test_book.py drive you.

"""
from __future__ import annotations

from collections import deque

from .domain import Order, Side


class OrderBook:
    def __init__(self) -> None:
        """Set up your containers for bids and asks.

        Hint: a natural shape is one mapping per side: price -> a FIFO queue of
        orders. collections.deque is a good FIFO. If you later want O(log n)
        best-price lookups, sortedcontainers.SortedDict is worth a look — but get
        it correct with plain dicts first.
        """
        self.bids = {}
        self.asks = {}

    def _side(self, side):
        return self.bids if side == Side.BUY else self.asks

    def add(self, order: Order) -> None:
        """Rest a limit order on its side at its price, at the BACK of that
        level's queue (it just arrived, so it has the lowest time priority there).
        """
        self._side(order.side).setdefault(order.price, deque()).append(order)


    def cancel(self, order_id: str) -> Order | None:
        """Remove a resting order by id. Return the removed order, or None if it
        wasn't found. Remember to clean up a price level once it's empty, or your
        best_bid/best_ask logic may report phantom prices.
        """
        for d in (self.bids, self.asks):
            for price, orders in list(d.items()):
                for order in list(orders):
                    if order.id == order_id:
                        orders.remove(order)
                        if not orders:
                            del d[price]
                        return order




    def best_bid(self) -> float | None:
        """Highest bid price that currently has resting volume, else None."""
        return max(self.bids) if self.bids else None

    def best_ask(self) -> float | None:
        """Lowest ask price that currently has resting volume, else None."""
        return min(self.asks) if self.asks else None

    def orders_at(self, side: Side, price: float) -> list[Order]:
        """The FIFO queue of resting orders at a given side + price, oldest first.
        Return [] if there are none. (Tests use this to inspect the book; the UI
        will later use it to render depth.)
        """
        return list(self._side(side).get(price, []))

    def snapshot(self) -> dict:
        def levels(side_map, *, descending):
            out = []
            for price in sorted(side_map, reverse=descending):
                queue = side_map[price]
                total = sum(o.remaining for o in queue)
                out.append({"price": price, "size": total, "count": len(queue)})
            return out

        bids = levels(self.bids, descending=True) # highest price
        asks = levels(self.asks, descending=False) # lowest first

        best_bids = bids[0]["price"] if bids else None
        best_asks = asks[0]["price"] if asks else None
        spread  = (best_asks - best_bids) if (best_bids is not None and best_asks is not None) else None
        mid     = (best_bids + best_asks) / 2 if (best_bids is not None and best_asks is not None) else None

        return {"bids": bids, "asks": asks,
                "best_bid": best_bids, "best_ask": best_asks,
                "spread": spread, "mid": mid}
