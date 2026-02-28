# Custom DNS Proxy Server

DNS proxy in Python: receives UDP queries, parses request (header + question), supports compressed format, forwards to upstream resolver, parses answer and builds response, and stores local cache.

## Run

```bash
uv run python main.py --resolver 8.8.8.8:53
```

Then from another terminal:

```bash
dig @127.0.0.1 -p 2053 example.com
```

## Scope (portfolio)

- Parse DNS query (header, question, compressed names)
- Structured response (dataclasses + encode to wire format)
- Forward to upstream resolver (`--resolver <ip>:<port>`)
- Store local cache

Requires Python 3.14+ (see `.python-version`).
