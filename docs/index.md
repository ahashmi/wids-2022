---
title: Home
layout: default
---

# Wids 2022 Phase II

<table class="pure-table pure-table-bordered">
    <thead>
        <tr>
            <th>Region</th>
            <th>States</th>
        </tr>
    </thead>
    <tbody>
        {%- for region in site.data.regions -%}
            <tr>
                <td>
                    {{ region[0] }}
                </td>
                <td>
                    {% for state in region[1] %}
                        <a href="states/{{ state }}.html">{{ state }}</a>
                    {% endfor %}
                </td>
            </tr>
        {%- endfor -%}
    </tbody>
</table>

