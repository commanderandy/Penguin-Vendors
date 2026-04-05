#!/usr/bin/env python3
"""
Sysco Shop GraphQL pricing lookup.

Usage:
    export SYSCO_AUTH_TOKEN="eyJ0eXAi..."
    export SYSCO_SYY_AUTH="eyJkYXRh..."
    python sysco_pricing.py

Tokens are session-based (~7 day expiry). To refresh:
  1. Log into shop.sysco.com
  2. DevTools → Network → any graphql request → Request Headers
  3. Copy authorization (drop "Bearer ") and syy-authorization values
"""

import json
import os
import sys
import requests

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_TOKEN = os.environ.get("SYSCO_AUTH_TOKEN", "")
SYY_AUTH   = os.environ.get("SYSCO_SYY_AUTH", "")

if not AUTH_TOKEN or not SYY_AUTH:
    sys.exit("Error: set SYSCO_AUTH_TOKEN and SYSCO_SYY_AUTH environment variables.")

ENDPOINT = "https://gateway-api.shop.sysco.com/graphql"

HEADERS = {
    "authorization":             f"Bearer {AUTH_TOKEN}",
    "syy-authorization":         SYY_AUTH,
    "apollographql-client-name": "SYSCO_SHOP_WEB",
    "content-type":              "application/json",
    "origin":                    "https://shop.sysco.com",
}

# ── Items to price ────────────────────────────────────────────────────────────

ITEMS = [
    "chicken breast",
    "romaine lettuce",
    "cheddar cheese",
    "olive oil",
    "pasta",
]

# ── Query ─────────────────────────────────────────────────────────────────────

QUERY = """
query SearchTypeaheadProductsWithPricingAndInventory(
  $params: ProductSearchQuery!,
  $isSkipPriceInfo: Boolean = false,
  $isIncludePriceInfoV2: Boolean = false
) {
  searchTypeaheadProducts(params: $params) {
    metaInfo { totalResults }
    results {
      productId
      priceInfo @skip(if: $isSkipPriceInfo) {
        case(newAttributeGroupDiscounts: true) { netPrice price minPrice maxPrice }
      }
      priceInfoV2 @include(if: $isIncludePriceInfoV2) {
        case(newAttributeGroupDiscounts: true) { netPrice price minPrice maxPrice }
      }
      productInfo {
        name
        brand { name }
        packSize { pack size uom }
      }
    }
  }
}
"""


def search(term, num=5):
    payload = {
        "operationName": "SearchTypeaheadProductsWithPricingAndInventory",
        "query": QUERY,
        "variables": {
            "params": {
                "q": term,
                "num": num,
                "start": 0,
                "facets": [],
            },
            "isSkipPriceInfo": False,
            "isIncludePriceInfoV2": True,
        },
    }
    r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def print_results(item, resp):
    errors = resp.get("errors")
    if errors:
        print(f"  API error: {errors[0].get('message')}")
        return

    results = (
        (resp.get("data") or {})
        .get("searchTypeaheadProducts", {})
        .get("results") or []
    )

    if not results:
        print("  No results found.")
        return

    for p in results:
        info        = p.get("productInfo") or {}
        pack_size   = info.get("packSize") or {}
        brand       = info.get("brand") or {}
        price_block = p.get("priceInfoV2") or p.get("priceInfo") or {}
        case_price  = price_block.get("case") or {}
        net_price   = case_price.get("netPrice") or case_price.get("price") or "N/A"

        print(f"  Name  : {info.get('name', 'N/A')}")
        print(f"  Brand : {brand.get('name', 'N/A')}")
        print(f"  ID    : {p.get('productId', 'N/A')}")
        pack = pack_size.get("pack", "")
        size = pack_size.get("size", "")
        uom  = pack_size.get("uom", "")
        print(f"  Pack  : {pack}/{size} {uom}")
        print(f"  Price : ${net_price} CS")
        print()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Sysco Shop pricing lookup")
    print("=" * 60)

    for item in ITEMS:
        print(f"\nItem: {item}")
        try:
            resp = search(item)
            print_results(item, resp)
        except requests.RequestException as exc:
            print(f"  Request error: {exc}")
