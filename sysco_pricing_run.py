#!/usr/bin/env python3
"""
Sysco Shop pricing lookup.
Query structure reverse-engineered from the live browser request.
"""

import json
import sys
import requests

ENDPOINT = "https://gateway-api.shop.sysco.com/graphql"

AUTH_TOKEN = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJlc3lzY29fdXNlcl90eXBlIjoiTm9ybWFsIiwi"
    "bmF0aXZlX3VzZXJfaWQiOiIwMTA1MjY3MzEiLCJjc3JmX3Rva2VuIjoiMGU5OWEyNDZmMjBkZjBi"
    "MzliYzgyOGY0Y2QyMTM5ODk1ODlmMDZjZSIsImN1c3RvbWVyX3V1aWQiOiIwMDAwMDAwMC0wMDAw"
    "LTAwMDAtNWE3OC01M2FkMTE4Nzc3ZmYiLCJpc3MiOiJjeC1wZXJtaXNzaW9uLXNlcnZpY2UiLCJj"
    "bGllbnRfY29va2llX25hbWUiOiJNU1NfU1RBVEVGVUwiLCJzaG9wX3VzZXJfdHlwZSI6ImN1c3Rv"
    "bWVyIiwiYXV0aF91c2VyX2lkIjoiMDB1MTczZHoxNDJZZ2JnZE41ZDciLCJzZXNzaW9uX2luZGV4"
    "IjoiXzYzZGM4OTNlYTMwOTU4NTlmMGE3OGFmNjM4NGUzZWRmYTFmMmQzMGUyMyIsInZpZCI6ImNt"
    "bmphYml2eTAxMXYwMWdzNHJoNTFyMW8iLCJjbGllbnRUeXBlIjoiV0VCIiwic3lzY29fY3VzdF9h"
    "cHBfc290ZiI6IiIsInNjb3BlIjoidmlld09yZGVycyIsImVzeXNjb19pZCI6IjAxMDUyNjczMSIs"
    "ImV4cCI6MTc3NTg0ODU5NSwiZmlyc3RfbmFtZSI6IkxlZSIsImlhdCI6MTc3NTI0Mzc5NSwiaXNf"
    "bXVsdGlfYnV5ZXIiOmZhbHNlLCJsYXN0X25hbWUiOiJNY0xlb2QiLCJjb3VudHJpZXMiOlsiVVMi"
    "XSwiaXNfbXVsdGlfYXBwcm92ZXIiOmZhbHNlLCJuYW1lX2lkIjoibGVlQHBlbmd1aW5kaW5lci5j"
    "b20iLCJ2ZXJzaW9uIjoiMy4wIiwiYXVkIjoiY3hzLXNob3AiLCJ1c2VyX2lkIjoiMDEwNTI2NzMx"
    "Iiwic2hvcF9hY2NvdW50X2lkIjoidXNibC0wMTAtNTI2NzMxIiwiZGVmYXVsdF9jb3VudHJ5Ijoi"
    "VVMifQ.aNhiJmp6oQXS9qKwkPi0cif_AQuBCQjyTktIi5Nn5objVrfE250LGZpwlFaMZvYrA_9QY"
    "_orQSncrk8XXqIX0Fpeenh-IAkUMCHCCKce4u1OY9pw97ESqD5V5rJj_GNeRrBcfVVBJq2oG4fI-"
    "5zfnvJ4pFdCBinOY2HiNduih16H2f8iZi2apNLvdKHxcFuuZf_iuZ9nxPviekgB-klzt7KePXz-8"
    "fOPHkdRW_adTgJYEmOiWLADQiC5ZTVNiHO6ANSHs4Mv7EJKifXn7Jj0gy17N96EqkNlwWGK9ACaU"
    "a3g5UAlFsALK00yTQEvbpY9n8j8oxznnYUTyIyHgkHk4w"
)

SYY_AUTH = (
    "eyJkYXRhIjp7InNob3BBY2NvdW50SWQiOiJ1c2JsLTAxMC01MjY3MzEiLCJzZWxsZXJzIjp7IlVT"
    "QkwiOnsic2l0ZUlkIjoiMDEwIiwic2VsbGVyQWNjb3VudElkIjoiNTI2NzMxIn19LCJzaG9wVXNl"
    "clR5cGUiOiJjdXN0b21lciIsImNvdW50cnkiOiJVUyJ9LCJfaGFzaCI6IjQ5ZDcyNGZmYjRiYTZi"
    "ZWNjNTBiZGQ2OTQyMjlkZTJhIn0="
)

HEADERS = {
    "authorization":             f"Bearer {AUTH_TOKEN}",
    "syy-authorization":         SYY_AUTH,
    "apollographql-client-name": "SYSCO_SHOP_WEB",
    "content-type":              "application/json",
    "origin":                    "https://shop.sysco.com",
}

ITEMS = [
    "chicken breast",
    "romaine lettuce",
    "cheddar cheese",
    "olive oil",
    "pasta",
]

# Exact query structure from the live browser request.
# - productInfo holds name, brand, packSize
# - priceInfoV2.case holds the case price (isSkipPriceInfo=false, isIncludePriceInfoV2=true)
QUERY = """
query SearchTypeaheadProductsWithPricingAndInventory(
  $params: ProductSearchQuery!,
  $isSkipPriceInfo: Boolean = false,
  $isIncludePriceInfoV2: Boolean = false,
  $isUseGraphStockStatusEnabled: Boolean = false
) {
  searchTypeaheadProducts(params: $params) {
    metaInfo {
      totalResults
    }
    results {
      productId
      siteId
      priceInfo @skip(if: $isSkipPriceInfo) {
        case(newAttributeGroupDiscounts: true) {
          netPrice
          price
          minPrice
          maxPrice
        }
      }
      priceInfoV2 @include(if: $isIncludePriceInfoV2) {
        case(newAttributeGroupDiscounts: true) {
          netPrice
          price
          minPrice
          maxPrice
        }
      }
      productInfo {
        name
        brand {
          name
        }
        packSize {
          pack
          size
          uom
        }
      }
    }
  }
}
"""


def search(term):
    payload = {
        "operationName": "SearchTypeaheadProductsWithPricingAndInventory",
        "query": QUERY,
        "variables": {
            "params": {
                "q": term,
                "num": 5,
                "start": 0,
            },
            "isSkipPriceInfo": False,
            "isIncludePriceInfoV2": True,
            "isUseGraphStockStatusEnabled": False,
        },
    }
    r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=15)
    return r.json()


print("=" * 60)
print("Sysco Shop pricing lookup")
print("=" * 60)

for item in ITEMS:
    print(f"\nItem: {item}")
    resp = search(item)

    errors = resp.get("errors")
    if errors:
        print(f"  API error: {errors[0].get('message')}")
        print(f"  Full response:\n{json.dumps(resp, indent=2)}")
        continue

    results = (
        (resp.get("data") or {})
        .get("searchTypeaheadProducts", {})
        .get("results") or []
    )

    if not results:
        print("  No results.")
        continue

    for p in results:
        info      = p.get("productInfo") or {}
        pack_size = info.get("packSize") or {}
        brand     = info.get("brand") or {}

        # priceInfoV2 preferred; fall back to priceInfo
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
