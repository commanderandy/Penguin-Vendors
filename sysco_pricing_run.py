#!/usr/bin/env python3
"""
Sysco Shop GraphQL API pricing lookup - standalone runner.
Tokens are embedded for one-off use. Do not commit this file.
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

SYY_AUTH = "eyJkYXRhIjp7InNob3BBY2NvdW50SWQiOiJ1c2JsLTAxMC01MjY3MzEiLCJzZWxsZXJzIjp7IlVTQkwiOnsic2l0ZUlkIjoiMDEwIiwic2VsbGVyQWNjb3VudElkIjoiNTI2NzMxIn19LCJzaG9wVXNlclR5cGUiOiJjdXN0b21lciIsImNvdW50cnkiOiJVUyJ9LCJfaGFzaCI6IjQ5ZDcyNGZmYjRiYTZiZWNjNTBiZGQ2OTQyMjlkZTJhIn0="

HEADERS = {
    "authorization":              f"Bearer {AUTH_TOKEN}",
    "syy-authorization":          SYY_AUTH,
    "apollographql-client-name":  "SYSCO_SHOP_WEB",
    "content-type":               "application/json",
    "origin":                     "https://shop.sysco.com",
}

SHOP_ACCOUNT_ID = "usbl-010-526731"
SITE_ID         = "010"

CANDIDATE_OPS = ["searchProducts", "searchProductsV2"]

PRODUCT_FIELDS = """
  supc
  name
  brand
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


def build_query(op_name, term):
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


def probe_operations(term="chicken breast"):
    print(f"\n{'='*60}")
    print(f"Probing GraphQL endpoint for term: '{term}'")
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
                print(f"  Non-JSON body:\n{resp.text[:800]}\n")
                body = {}

            data    = body.get("data") or {}
            op_data = data.get(op) or {}
            products = op_data.get("products") if isinstance(op_data, dict) else None
            if products:
                print(f"  *** SUCCESS: '{op}' returned {len(products)} product(s) ***\n")
                return op

        except requests.RequestException as exc:
            print(f"  Request error: {exc}\n")

    print("No operation name returned product data.")
    return None


def fetch_prices(items, op_name):
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
                print(f"  Name : {p.get('name', 'N/A')}")
                print(f"  SUPC : {p.get('supc', 'N/A')}")
                print(f"  Pack : {p.get('pack', '')}  Size: {p.get('size', '')}")
                print(f"  Price: {price}")
                print()
        except Exception as exc:
            print(f"  Error fetching '{item}': {exc}\n")


ITEMS_TO_PRICE = [
    "chicken breast",
    "romaine lettuce",
    "cheddar cheese",
    "olive oil",
    "pasta",
]

if __name__ == "__main__":
    working_op = probe_operations("chicken breast")
    if working_op:
        fetch_prices(ITEMS_TO_PRICE, working_op)
    else:
        sys.exit(1)
