# Pasted Amazon text (the free route for method 4)

One folder per product, named after it:

```
inputs/amazon/system-design-interview-vol-1/reviews.txt
inputs/amazon/system-design-interview-vol-1/listing.txt
```

- `reviews.txt`: open the product's reviews page in your browser, select the reviews, copy and paste.
  Each review is found by its "N out of 5 stars" line; ratings and "N people found this helpful" are
  read automatically. Paste the 1-3 star pages too (that is where the objections are).
- `listing.txt`: the title, the "About this item" bullets and the description, pasted as-is.

Then run `bin/pipeline import-amazon` (or `bin/pipeline run`).
With an `APIFY_TOKEN` in `.env`, `bin/pipeline collect --pillar marketplace` pulls the products
listed in `config/fanout.toml` instead.
