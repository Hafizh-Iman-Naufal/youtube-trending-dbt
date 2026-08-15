{#
    Deterministic surrogate key from (region_code, video_id, trending_date).
    Uses dbt_utils.generate_surrogate_key for cross-adapter compat.
#}
{% macro generate_observation_key() %}
    {{ dbt_utils.generate_surrogate_key(['region_code', 'video_id', 'trending_date']) }}
{% endmacro %}
