-- Core dimension: one row per supported region. Source = seed.
select
    {{ dbt_utils.generate_surrogate_key(['region_code']) }} as region_key,
    region_code,
    region_name,
    locale,
    language_code
from {{ ref('region_metadata') }}
