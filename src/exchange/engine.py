"""MatchingEngine — YOUR code goes here.

The engine is the *algorithm*. It takes an incoming order, matches it against the
opposite side of the book using PRICE-TIME PRIORITY, produces Trades, and updates
the book. Implement submit() and cancel() so tests/test_engine.py pass.

----------------------------------------------------------------------------
The matching algorithm for submit(order), in words (you write the code):

  1. A BUY matches against asks; a SELL matches against bids.

  2. Loop while the incoming order still has remaining quantity AND there is an
     opposing best price it is willing to trade at:
        - LIMIT  buy  crosses while best_ask <= order.price
        - LIMIT  sell crosses while best_bid >= order.price
        - MARKET orders cross as long as ANY opposing liquidity exists.

  3. Take the order at the FRONT of the best opposing level — that's the MAKER
     (oldest = highest time priority). Then:
        - trade_qty   = min(incoming.remaining, maker.remaining)
        - trade_price = the MAKER's price   (the passive order sets the price)
        - reduce BOTH orders' remaining by trade_qty
        - record a Trade(taker = incoming, maker = resting)
        - if the maker is now fully filled, remove it from the book and continue
          to the next resting order / next price level.

  4. When the loop ends:
        - LIMIT  with remaining > 0  -> rest the remainder on the book.
        - MARKET with remaining > 0  -> do NOT rest it; it goes unfilled.
          (Decide how you signal that — a status change, or just stop.)

  5. Return the list of Trades produced by THIS call (possibly empty). A later
     phase will stream these out over WebSocket to the UI.
----------------------------------------------------------------------------

Watch out for: recomputing the best price each loop iteration (it changes as you
consume levels), and not mutating a list while iterating it.
"""
from __future__ import annotations

from .book import OrderBook
from .domain import Order, Trade


class MatchingEngine:
    def __init__(self, book: OrderBook | None = None) -> None:
        self.book = book or OrderBook()

    def submit(self, order: Order) -> list[Trade]:
        """Match `order` against the book, returning the trades it generates."""
        raise NotImplementedError

    def cancel(self, order_id: str) -> Order | None:
        """Cancel a resting order. Delegate to the book; return it or None."""
        raise NotImplementedError
