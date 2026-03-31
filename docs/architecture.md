# Architecture Summary

## Control plane
- Admin dashboard
- FastAPI backend
- PostgreSQL
- Redis (future job / event use)

## Execution plane
- Per-account worker
- MT5 adapter
- Strategy engine
- Risk manager
- Event/log publishing back to API

## Account modes
- **Monitor mode:** Investor password only, read-only status and analytics
- **Execute mode:** Trading-capable account session, bot can place orders

## Strategy constraints
- XAUUSD only
- M5 / M15 entries
- H1 / H4 trend bias
- Trade only with clear trend
- Liquidity sweep + BOS + OB/FVG retrace
- Session + news + risk filters
