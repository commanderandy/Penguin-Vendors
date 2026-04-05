# Penguin Vendors — Project Context for Claude Code

## What this project is

Penguin Diner (Sysco account `usbl-010-526731`, site `010`, seller `526731`) needs a Python script that queries the **Sysco Shop GraphQL API** for live product pricing. The goal is to accept a list of items (e.g. "chicken breast", "romaine lettuce") and return name, pack size, and price for each.

## Working API details

**Endpoint:** `POST https://gateway-api.shop.sysco.com/graphql`

**Required headers:**
```
authorization: Bearer <jwt>
syy-authorization: <base64-encoded session token>
apollographql-client-name: SYSCO_SHOP_WEB
content-type: application/json
origin: https://shop.sysco.com
```

Tokens are session-based and expire (Bearer token lasts ~7 days). To refresh:
1. Log into shop.sysco.com in a browser
2. Open DevTools → Network → filter Fetch/XHR → click any `graphql` request
3. Copy `authorization` and `syy-authorization` from Request Headers

## Working GraphQL query (reverse-engineered from browser)

The correct operation is `searchTypeaheadProducts` with operation name `SearchTypeaheadProductsWithPricingAndInventory`.

```graphql
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
```

**Variables:**
```json
{
  "params": {
    "q": "<search term>",
    "num": 5,
    "start": 0,
    "facets": []
  },
  "isSkipPriceInfo": false,
  "isIncludePriceInfoV2": true
}
```

Key field paths in the response:
- Product ID (SUPC): `results[].productId`
- Name: `results[].productInfo.name`
- Brand: `results[].productInfo.brand.name`
- Pack/size: `results[].productInfo.packSize.{pack, size, uom}`
- Price: `results[].priceInfoV2.case.netPrice`

## Schema discoveries (from error messages during development)

- `searchProducts` and `searchProductsV2` exist but use a flat `results` array with different type names (`Product`, `CatalogProduct`) — not the right operations for this use case
- `getProducts` takes a `products: ProductQuery!` argument — it's a by-ID lookup, not search
- `searchTypeaheadProducts` is what the browser actually uses for the catalog search page
- `ProductSearchQuery` requires: `q` (search term), `facets: []` (required even if empty), `num`, `start`
- Pricing lives in `priceInfoV2` (v1 `priceInfo` exists but is skipped by the browser)

## Files

- `sysco_pricing.py` — production script, reads tokens from env vars `SYSCO_AUTH_TOKEN` and `SYSCO_SYY_AUTH`
- `sysco_pricing_run.py` — standalone runner with tokens embedded (do not commit tokens to main branch)

## Current status

The query structure is confirmed working (auth validated, schema validated, `facets: []` required field identified). The next run should return live product data.

## Next steps

1. Verify the script returns live pricing data end-to-end
2. Expand `ITEMS` list to the full Penguin Diner product list
3. Consider outputting results to CSV for use in menu costing
4. Tokens need refreshing periodically — could automate via Selenium/Playwright session login

## Development branch

`claude/sysco-pricing-api-script-glPy3`
