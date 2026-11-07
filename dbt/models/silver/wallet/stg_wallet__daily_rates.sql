select
    rate_date,
    cast(annual_rate as float64) as annual_rate
from {{ source('wallet', 'daily_rates') }}
