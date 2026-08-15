{#  Returns numerator / denominator, NULL for NULL or zero denominator.
    Do NOT default to 0 — metric semantics treat division-by-zero as
    "not meaningful" rather than "zero". #}
{% macro safe_divide(numerator, denominator) %}
    case
        when {{ denominator }} is null or {{ denominator }} = 0 then null
        when {{ numerator }} is null then null
        else cast({{ numerator }} as double) / cast({{ denominator }} as double)
    end
{% endmacro %}
