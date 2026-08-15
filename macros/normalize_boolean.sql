{#
    Normalize a raw boolean string column ('True'/'False' etc.) to BOOLEAN.
    Returns NULL for unrecognized values rather than silently coercing.
#}
{% macro normalize_boolean(col) %}
    case
        when lower(trim({{ col }})) in ('true', 't', '1') then true
        when lower(trim({{ col }})) in ('false', 'f', '0') then false
        else null
    end
{% endmacro %}
