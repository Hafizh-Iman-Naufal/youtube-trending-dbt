-- Staging model: category metadata, all regions.
-- Unpivots the per-region raw category tables into one set.

with ca as (select * from {{ source('youtube_raw', 'raw_youtube_categories__CA') }}),
     de as (select * from {{ source('youtube_raw', 'raw_youtube_categories__DE') }}),
     fr as (select * from {{ source('youtube_raw', 'raw_youtube_categories__FR') }}),
     gb as (select * from {{ source('youtube_raw', 'raw_youtube_categories__GB') }}),
     in_ as (select * from {{ source('youtube_raw', 'raw_youtube_categories__IN') }}),
     jp as (select * from {{ source('youtube_raw', 'raw_youtube_categories__JP') }}),
     kr as (select * from {{ source('youtube_raw', 'raw_youtube_categories__KR') }}),
     mx as (select * from {{ source('youtube_raw', 'raw_youtube_categories__MX') }}),
     ru as (select * from {{ source('youtube_raw', 'raw_youtube_categories__RU') }}),
     us as (select * from {{ source('youtube_raw', 'raw_youtube_categories__US') }})

select
    _source_region as region_code,
    cast(category_id as varchar) as category_id,
    category_title,
    category_channel_id,
    assignable,
    _source_file,
    _loaded_at
from ca
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from de
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from fr
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from gb
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from in_
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from jp
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from kr
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from mx
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from ru
union all
select _source_region, cast(category_id as varchar), category_title, category_channel_id, assignable, _source_file, _loaded_at from us
