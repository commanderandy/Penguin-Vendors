#!/usr/bin/env python3
"""
Sysco Shop GraphQL pricing lookup.

Phase 1 — Schema introspection: asks the API itself for the exact field names
           of ProductSearchQuery, the result wrapper, and the product type.
Phase 2 — Price fetch: uses those discovered names to run the real search.
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

SHOP_ACCOUNT_ID = "usbl-010-526731"
SITE_ID         = "010"

ITEMS = [
    "chicken breast",
    "romaine lettuce",
    "cheddar cheese",
    "olive oil",
    "pasta",
]


def post(payload):
    r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=15)
    return r.json()


def unwrap_type(t):
    """Follow NON_NULL / LIST wrappers to get the named type."""
    if t is None:
        return None
    if t.get("name"):
        return t["name"]
    return unwrap_type(t.get("ofType"))


# ── Phase 1: introspect every type we'll need ─────────────────────────────────

print("=" * 60)
print("Phase 1: schema introspection")
print("=" * 60)

intro = post({
    "query": """
    {
      searchInput:   __type(name: "ProductSearchQuery") {
        inputFields { name type { kind name ofType { kind name ofType { kind name } } } }
      }
      resultV2:      __type(name: "ProductSearchResultV2") {
        fields       { name type { kind name ofType { kind name ofType { kind name } } } }
      }
      result:        __type(name: "ProductSearchResult") {
        fields       { name type { kind name ofType { kind name ofType { kind name } } } }
      }
    }
    """
})

print(json.dumps(intro, indent=2))
data = intro.get("data") or {}

# -- ProductSearchQuery input fields --
pq_raw   = (data.get("searchInput") or {}).get("inputFields") or []
pq_names = [f["name"] for f in pq_raw]
print(f"\nProductSearchQuery input fields : {pq_names}")

# -- Decide which search op + result wrapper to use --
# Prefer V2; fall back to V1.
rv2_raw  = (data.get("resultV2") or {}).get("fields") or []
rv1_raw  = (data.get("result")   or {}).get("fields") or []

if rv2_raw:
    op_name      = "searchProductsV2"
    result_flds  = {f["name"]: f for f in rv2_raw}
else:
    op_name      = "searchProducts"
    result_flds  = {f["name"]: f for f in rv1_raw}

print(f"Using operation            : {op_name}")
print(f"Result wrapper fields      : {list(result_flds.keys())}")

# The list field is "results" (confirmed by earlier error messages).
# Find the element type name so we can introspect it.
results_field = result_flds.get("results") or {}
product_type  = unwrap_type(results_field.get("type"))
print(f"Product element type       : {product_type}")

# -- Introspect the product type --
prod_intro = post({
    "query": "query($n:String!){ __type(name:$n){ fields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } } }",
    "variables": {"n": product_type or "Product"}
})
print(f"\n{product_type} fields:")
print(json.dumps(prod_intro, indent=2))

prod_fields_raw = ((prod_intro.get("data") or {}).get("__type") or {}).get("fields") or []
prod_field_names = [f["name"] for f in prod_fields_raw]
print(f"\nAll product fields: {prod_field_names}")

# Pick the fields we care about — keep only ones that actually exist.
WANT_SCALAR  = ["supc", "name", "brand", "pack", "size", "description"]
WANT_OBJECTS = {
    # candidate name → sub-fields to request
    "priceObject": "price netPrice listPrice priceType",
    "pricing":     "price netPrice listPrice",
    "price":       "amount currency",
}

safe_scalars = [f for f in WANT_SCALAR if f in prod_field_names]
safe_objects = {k: v for k, v in WANT_OBJECTS.items() if k in prod_field_names}

print(f"\nScalar fields we'll request : {safe_scalars}")
print(f"Object fields we'll request : {list(safe_objects.keys())}")

# -- Decide which params key carries the search term --
TERM_CANDIDATES = ["keyword", "searchTerm", "query", "term", "q"]
term_key = next((k for k in TERM_CANDIDATES if k in pq_names), None)

# Also find siteId / accountId keys
site_key    = next((k for k in ["siteId", "site", "opco"] if k in pq_names), None)
account_key = next((k for k in ["accountId", "shopAccountId", "customerId"] if k in pq_names), None)
page_key     = next((k for k in ["page", "pageNumber", "offset"] if k in pq_names), None)
pagesize_key = next((k for k in ["pageSize", "size", "perPage", "first", "limit"] if k in pq_names), None)

print(f"\nParam key for search term  : {term_key}")
print(f"Param key for siteId       : {site_key}")
print(f"Param key for accountId    : {account_key}")
print(f"Param key for page         : {page_key}")
print(f"Param key for pageSize     : {pagesize_key}")

if not term_key:
    print("\nERROR: could not identify the search-term field in ProductSearchQuery.")
    print(f"Available fields: {pq_names}")
    sys.exit(1)


# ── Phase 2: search and print prices ─────────────────────────────────────────

def build_product_selection():
    lines = safe_scalars[:]
    for obj_field, sub_fields in safe_objects.items():
        lines.append(f"{obj_field} {{ {sub_fields} }}")
    return "\n          ".join(lines)


def search(term):
    params = {term_key: term}
    if site_key:
        params[site_key] = SITE_ID
    if account_key:
        params[account_key] = SHOP_ACCOUNT_ID
    if page_key:
        params[page_key] = 1
    if pagesize_key:
        params[pagesize_key] = 5

    query = f"""
    query {op_name}($params: ProductSearchQuery!) {{
      {op_name}(params: $params) {{
        results {{
          {build_product_selection()}
        }}
      }}
    }}
    """
    return post({"operationName": op_name, "query": query, "variables": {"params": params}})


print("\n" + "=" * 60)
print("Phase 2: price lookup")
print("=" * 60)

for item in ITEMS:
    print(f"\nItem: {item}")
    resp = search(item)
    items_list = ((resp.get("data") or {}).get(op_name) or {}).get("results") or []
    if not items_list:
        errs = resp.get("errors")
        print(f"  No results. Response: {json.dumps(resp, indent=2)}")
        continue
    for p in items_list:
        # Find price — try known price object names then fall back to any key with 'price'
        price = "N/A"
        for obj_key in safe_objects:
            po = p.get(obj_key)
            if isinstance(po, dict):
                price = po.get("netPrice") or po.get("price") or po.get("amount") or "N/A"
                break
        if price == "N/A":
            # try scalar price fields
            price = p.get("netPrice") or p.get("price") or "N/A"

        print(f"  Name : {p.get('name', 'N/A')}")
        print(f"  SUPC : {p.get('supc', 'N/A')}")
        print(f"  Pack : {p.get('pack', '')}  Size: {p.get('size', '')}")
        print(f"  Price: {price}")
