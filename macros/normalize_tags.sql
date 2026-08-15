{#  Normalize a raw tag string into two SQL fragments:
    `tags_normalized` and `tag_count`. The macro returns a Jinja tuple
    so callers can do `{% set nt = normalize_tags('col') %}` and reference
    `nt.normalized` and `nt.count`. #}
{% macro normalize_tags(raw_col) %}
    {% set normalized %}
        case
            when {{ raw_col }} is null or trim({{ raw_col }}) = '' then null
            when lower(trim({{ raw_col }})) = '[none]' then null
            else regexp_replace(
                regexp_replace({{ raw_col }}, '"', '', 'g'),
                '\|+', '|', 'g'
            )
        end
    {% endset %}
    {% set count %}
        case
            when {{ raw_col }} is null or trim({{ raw_col }}) = '' then 0
            when lower(trim({{ raw_col }})) = '[none]' then 0
            else
                length(regexp_replace(
                    regexp_replace({{ raw_col }}, '"', '', 'g'),
                    '\|+', '|', 'g'
                ))
                - length(replace(
                    regexp_replace({{ raw_col }}, '"', '', 'g'),
                    '|', ''
                ))
                + 1
        end
    {% endset %}
    {{ return({'normalized': normalized, 'count': count}) }}
{% endmacro %}
