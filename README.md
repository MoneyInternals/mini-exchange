# mini-exchange

A mini-exchange built from scratch: a price-time-priority **matching engine**,
an **order book**, simulated **participants/bots** generating flow, a live **tick
feed + API**, a **candlestick chart**, and a **settlement ledger** — added one
feature at a time.

> Part of the **Money Internals** series **Build an Exchange**.
> 📺 [Money Internals](https://youtube.com/@MoneyInternals)

> Scaffolding and tests are AI-assisted; the **matching engine, order book, and
> all core logic are my own work.**

This is a build-in-public / portfolio project and the backbone of the series.
Each episode adds one mechanism to this same codebase, so the repo grows with
the series. The distribution is named `mini-exchange`; the importable package
is `exchange` (distribution ≠ import name is standard).

## Episodes

| Episode | Mechanism | Tag |
|---|---|---|
| 1 — The order book | Bids, asks, spread, depth | `ep01-order-book` |

Check out a tag to see the repo exactly as it stood at that episode:
`git checkout ep01-order-book`

**State as of `ep01-order-book`:** the order book (`book.py`) is implemented
and tested; the matching engine (`engine.py`) is stubbed — that's episode 2.

## Want to learn it properly? Build it yourself

The repo is structured so the tests are the spec: the shared types and the
failing tests are given, and the interesting logic is written against them.
That's how it was built, and you can rebuild it the same way — delete the
bodies of `book.py` (and later `engine.py`), run `pytest`, and implement until
green.

| File | Status |
|---|---|
| `src/exchange/domain.py` | **Given** — the shared types (the contract) |
| `src/exchange/book.py` | The order book (episode 1) |
| `src/exchange/engine.py` | The matching engine — stubbed until episode 2 |
| `tests/` | **Given** — the tests that define "correct" |

## Run it

```bash
cd mini-exchange
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # or: pip install pytest

pytest tests/test_book.py -v    # green as of episode 1
pytest tests/test_engine.py -v  # fails until the engine exists (episode 2)
```

To open the terminal UI (the one on screen in the videos):

```bash
./frontend/record.sh            # Chrome app-mode window, 2560x1440
# or just open frontend/order-book-terminal.html in any browser
```

The frontend currently runs standalone on an in-page JS book that mirrors
`book.py`; it gets wired to the Python engine over an API in a later phase.

## Build order (Phase 1 — the core)

Do these in order; each leans on the last. Let the tests drive you.

1. **`OrderBook.__init__` + `add` + `orders_at`** → pass the first few `test_book` cases.
2. **`best_bid` / `best_ask`** → price-priority lookups.
3. **`cancel`** → and remember to drop empty price levels.
4. **`MatchingEngine.submit`** → the heart. Follow the prose algorithm in
   `engine.py`. Get a simple full cross trading first, then partial fills, then
   price-time priority, then market sweeps.
5. **`MatchingEngine.cancel`** → delegate to the book.

When `pytest` is all green, Phase 1 is done — and you have a correct matching
engine, which is the genuinely impressive part of the whole project.

## One real design decision (don't skip it)

`price` is a `float` right now. The tests use clean values (100.0, 101.0) so that
is safe — but for real money, float equality bites. Before Phase 2, decide:
keep float, switch to `Decimal`, or use **integer ticks** (store price as an int
number of minimum increments). Write down why. This is exactly the kind of
trade-off a Staff-level reviewer probes.

## Roadmap (later phases)

- **Phase 2 — Simulation.** Bot agents (noise traders, a market maker, a
  momentum trader) + a clock that steps the market so flow appears on its own.
- **Phase 3 — API.** FastAPI: REST to place/cancel orders and read the book;
  WebSocket to stream book + trade updates to the UI.
- **Phase 4 — Market data.** Aggregate trades into OHLC candles for the chart.
- **Phase 5 — UI.** Wire the terminal to the API: live depth ladder,
  candlestick chart, and the order ticket driving the real engine.

## Layout

```
mini-exchange/
├── pyproject.toml
├── README.md
├── src/exchange/
│   ├── domain.py     # given: Side, OrderType, OrderStatus, Order, Trade
│   ├── book.py       # the OrderBook (episode 1)
│   └── engine.py     # the MatchingEngine (stubbed — episode 2)
├── frontend/
│   ├── order-book-terminal.html   # standalone terminal UI
│   └── record.sh                  # opens it at recording size
└── tests/
    ├── test_book.py
    ├── test_snapshot.py
    └── test_engine.py
```

---

*Educational project — a market simulator built to explain mechanics. Nothing
here is trading software, investment advice, or a recommendation to buy or
sell anything.*