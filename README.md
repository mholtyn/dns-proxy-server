# Custom DNS Proxy Server

DNS proxy in Python: receives UDP queries, parses request (header + question), builds and sends a response (echo question + static A record). Prepared for extending with upstream forwarding and optional cache.

## Run

```bash
uv run python app/main.py
```

Then from another terminal:

```bash
dig @127.0.0.1 -p 2053 +noedns example.com
```

## Scope (portfolio)

- Parse DNS query (header, question)
- Structured response (dataclasses + encode to wire format)
- Single upstream + cache: planned

Requires Python 3.14+ (see `.python-version`).
