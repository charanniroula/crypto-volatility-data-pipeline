WITH hourly_prices AS(    
    SELECT 
        CAST(timestamp AS TIMESTAMP) AS date_time,
        asset_id,
        price_usd,
        -- shows price from previous hour
        LAG(price_usd, 1) OVER (
            PARTITION BY asset_id
            ORDER BY timestamp
        ) AS prev_hour_price
    FROM crypto_market_data
)
SELECT 
    date_time,
    asset_id,
    price_usd,
    prev_hour_price,
    ROUND(((price_usd - prev_hour_price) / prev_hour_price) * 100.0, 4) AS hourly_percent_change
FROM
    hourly_prices
WHERE 
    prev_hour_price IS NOT NULL
