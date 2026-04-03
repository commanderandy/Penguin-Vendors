#!/usr/bin/env python3
"""
Sysco Shop GraphQL API pricing lookup script.
Probes multiple operation names to find the correct product search query,
then fetches name, pack size, and price for a list of items.
"""

import json
import sys
import requests

# ── Configuration ────────────────────────────────────────────────────────────

ENDPOINT = "https://gateway-api.shop.sysco.com/graphql"

# Replace the placeholder values below with your actual tokens.
AUTH_TOKEN   = "REPLACE_WITH_BEARER_TOKEN"
SYY_AUTH     = "REPLACE_WITH_SYY_AUTHORIZATION_VALUE"

HEADERS = {
    "authorization":           f"Bearer {AUTH_TOKEN}",
    "syy-authorization":       SYY_AUTH,
    "apollographql-client-name": "SYSCO_SHOP_WEB",
    "content-type":            "application/json",
    "origin":                  "https://shop.sysco.com",
}

# Account / site identifiers
SHOP_ACCOUNT_ID = "usbl-010-526731"
SITE_ID         = "010"
SELLER_ACCOUNT  = "526731"

# Operation names to probe, in order
CANDIDATE_OPS = [
    "searchV2",
    "catalogSearch",
    "productSearch",
    "getProducts",
    "search",
    "SearchProducts",
]

# ── GraphQL fragments ────────────────────────────────────────────────────────

# Core product fields we care about (used in every query variant)
PRODUCT_FIELDS = """
  supc
  name
  brand
  averageWeightPerCase
  pack
  size
  priceObject {
    price
    priceType
    netPrice
    listPrice
    splitPrice
  }
"""

def build_query(op_name: str, term: str) -> dict:
    """Build a GraphQL request body for the given operation name."""
    # Try several plausible query shapes; GraphQL will reject unknown ones.
    query = f"""
    query {op_name}($searchTerm: String!, $siteId: String, $accountId: String) {{
      {op_name}(
        searchTerm: $searchTerm
        siteId: $siteId
        accountId: $accountId
        pageSize: 5
        page: 1
      ) {{
        products {{
          {PRODUCT_FIELDS}
        }}
        totalCount
      }}
    }}
    """
    return {
        "operationName": op_name,
        "query": query,
        "variables": {
            "searchTerm": term,
            "siteId": SITE_ID,
            "accountId": SHOP_ACCOUNT_ID,
        },
    }


def probe_operations(term: str = "chicken breast") -> str | None:
    """
    Try each candidate operation name.  Print the raw response for each.
    Return the first operation name that yields product data, or None.
    """
    print(f"\n{'='*60}")
    print(f"Probing GraphQL endpoint for term: '{term}'")
    print(f"Endpoint: {ENDPOINT}")
    print(f"{'='*60}\n")

    for op in CANDIDATE_OPS:
        print(f"--- Trying operationName: {op} ---")
        payload = build_query(op, term)
        try:
            resp = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=15)
            print(f"  HTTP {resp.status_code}")
            try:
                body = resp.json()
                print(f"  Response JSON:\n{json.dumps(body, indent=2)}\n")
            except ValueError:
                print(f"  Non-JSON response body:\n{resp.text[:500]}\n")
                body = {}

            # Check for usable product data
            data = body.get("data") or {}
            op_data = data.get(op) or {}
            products = op_data.get("products") if isinstance(op_data, dict) else None
            if products:
                print(f"  *** SUCCESS: '{op}' returned {len(products)} product(s) ***\n")
                return op

        except requests.RequestException as exc:
            print(f"  Request error: {exc}\n")

    print("No operation name returned product data.")
    return None


# ── Pricing lookup ───────────────────────────────────────────────────────────

def fetch_prices(items: list[str], op_name: str) -> None:
    """
    For each item in `items`, call the working operation and print
    name, pack size, and price.
    """
    print(f"\n{'='*60}")
    print(f"Fetching prices using operationName: '{op_name}'")
    print(f"{'='*60}\n")

    for item in items:
        print(f"Item: {item}")
        payload = build_query(op_name, item)
        try:
            resp = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=15)
            body = resp.json()
            products = (body.get("data", {}).get(op_name) or {}).get("products", [])
            if not products:
                print("  No products found.\n")
                continue
            for p in products:
                price_obj = p.get("priceObject") or {}
                price = (
                    price_obj.get("netPrice")
                    or price_obj.get("price")
                    or price_obj.get("listPrice")
                    or "N/A"
                )
                pack  = p.get("pack", "")
                size  = p.get("size", "")
                print(f"  Name : {p.get('name', 'N/A')}")
                print(f"  SUPC : {p.get('supc', 'N/A')}")
                print(f"  Pack : {pack}  Size: {size}")
                print(f"  Price: {price}")
                print()
        except Exception as exc:
            print(f"  Error fetching '{item}': {exc}\n")


# ── Main ─────────────────────────────────────────────────────────────────────

ITEMS_TO_PRICE = [
    "chicken breast",
    "romaine lettuce",
    "cheddar cheese",
    "olive oil",
    "pasta",
]

if __name__ == "__main__":
    # Phase 1: probe to find the working operation name
    working_op = probe_operations("chicken breast")

    # Phase 2: if found, fetch prices for the full item list
    if working_op:
        fetch_prices(ITEMS_TO_PRICE, working_op)
    else:
        print("\nSkipping price fetch — no working operation found.")
        sys.exit(1)
