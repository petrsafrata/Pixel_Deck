# Web Configuration Schema

Pixel Deck uses `FieldSpec` metadata to describe editable scene configuration. The frontend is schema-driven rather than scene-specific.

## Supported field types

| Type | UI purpose |
|---|---|
| `boolean` | Toggle |
| `number` | Numeric input |
| `color` | Color editor |
| `text` | Text input |
| `select` | Dropdown |
| `string_list` | String list |
| `image-gallery` | Image gallery |

## Shared fields

| Field | Purpose |
|---|---|
| `duration_s` | Scene duration |
| `refresh_s` | Refresh interval |
| `fps` | Frame rate |
| `background` | Background color |
| `font.primary_color` | Primary text color |
| `font.secondary_color` | Secondary text color |

A `FieldSpec` can also define labels, descriptions, groups, units, validation limits, step size, placeholders, options, rows, multiline behavior, required state, and numeric type.

## Workflow

1. Define or reuse a `FieldSpec`.
2. Include it in the scene field specifications.
3. Expose it through scene metadata.
4. The backend returns the schema to React.
5. React generates the appropriate control.

No scene-specific React form is required for supported field types.
