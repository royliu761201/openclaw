---
name: currency-exchange
description: Get current and historical exchange rates for foreign currencies using the free Frankfurter API (ECB data). No API key required. Use python3 to run the script.
homepage: https://www.frankfurter.app
metadata:
  openclaw:
    emoji: �
    requires:
      bins: ["python3"]
---

# Currency Exchange Skill

Free, open-source currency data from the European Central Bank via Frankfurter API.

## CLI Usage

Convert currency amounts using the command line:

```bash
# Get exchange rate from USD to CNY
python3 skills/currency-exchange/scripts/currency_tool.py get_rate --from USD --to CNY

# Convert 100 USD to EUR
python3 skills/currency-exchange/scripts/currency_tool.py get_rate --from USD --to EUR --amount 100

# Convert CAD to JPY
python3 skills/currency-exchange/scripts/currency_tool.py get_rate --from CAD --to JPY --amount 50
```

## Parameters

- `--from`: Source currency code (e.g., USD, EUR, CAD)
- `--to`: Target currency code (e.g., CNY, JPY, GBP)
- `--amount`: Amount to convert (optional, default: 1.0)

## Output

Returns JSON with exchange rate information:

```json
{
  "base": "USD",
  "target": "CNY",
  "rate": 690.86,
  "amount": 100.0,
  "result": 690.86,
  "date": "2026-02-13"
}
```
