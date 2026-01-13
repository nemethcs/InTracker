# Color System

Color palette and usage guidelines for InTracker UI components.

## Color Palette

Based on Cursor/Linear/Vercel/Stripe aesthetic with Deep Indigo/Electric Blue primary and Cyan accents.

### Primary Colors

| Color | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| **Primary** | `#2563EB` (Electric Blue) | `hsl(217, 91%, 65%)` | Primary actions, links, focus states |
| **Accent** | `#22D3EE` (Cyan) | `hsl(188, 78%, 63%)` | Accent elements, highlights, secondary actions |
| **Destructive** | `hsl(0, 84%, 60%)` | `hsl(0, 72%, 51%)` | Errors, destructive actions, warnings |

### Semantic Colors

| Color | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| **Background** | `#FFFFFF` | `#0F172A` (Dark Navy) | Main background |
| **Foreground** | `#0F172A` (Dark Navy) | `hsl(210, 40%, 98%)` | Primary text |
| **Card** | `#FFFFFF` | `hsl(217, 33%, 15%)` | Card backgrounds |
| **Muted** | `#E5E7EB` | `hsl(217, 33%, 20%)` | Muted backgrounds, borders |
| **Border** | `#E5E7EB` | `hsl(217, 33%, 25%)` | Borders, dividers |

## Usage Guidelines

### Primary Color (`primary`)

**When to use:**
- Primary action buttons
- Links and navigation
- Focus rings and active states
- Important UI elements
- Progress indicators

**When NOT to use:**
- Background colors (too intense)
- Large text blocks (use foreground instead)
- Decorative elements (use accent instead)

**Examples:**
```tsx
// Primary button
<Button variant="default">Save</Button>

// Link
<a className="text-primary hover:underline">Learn more</a>

// Focus ring
<input className="focus-visible:ring-ring" />
```

### Accent Color (`accent`)

**When to use:**
- Secondary actions
- Highlights and badges
- Hover states on secondary elements
- Decorative accents
- Progress indicators (alternative)

**When NOT to use:**
- Primary actions (use primary instead)
- Error states (use destructive instead)
- Large backgrounds

**Examples:**
```tsx
// Accent badge
<Badge variant="accent">New</Badge>

// Hover state
<Button variant="outline" className="hover:bg-accent">
  Secondary Action
</Button>
```

### Destructive Color (`destructive`)

**When to use:**
- Error messages
- Destructive actions (delete, remove)
- Validation errors
- Warning states
- Critical alerts

**When NOT to use:**
- Primary actions
- Success states
- Neutral information

**Examples:**
```tsx
// Error state
<Input error className="border-destructive" />

// Destructive button
<Button variant="destructive">Delete</Button>

// Error message
<div className="text-destructive">This field is required</div>
```

### Muted Colors (`muted`)

**When to use:**
- Secondary text
- Placeholders
- Disabled states
- Subtle backgrounds
- Borders and dividers

**Examples:**
```tsx
// Muted text
<p className="text-muted-foreground">Optional description</p>

// Muted background
<div className="bg-muted">Subtle background</div>

// Disabled input
<input disabled className="bg-muted/50" />
```

## Color Tokens

Always use CSS variables for colors to ensure consistency and dark mode support:

```tsx
// ✅ Good - Uses design system tokens
<div className="bg-primary text-primary-foreground">
<div className="text-destructive">
<div className="border-border">

// ❌ Bad - Hardcoded colors
<div className="bg-blue-500">
<div className="text-red-500">
<div style={{ color: '#2563EB' }}>
```

## Dark Mode

All colors automatically adapt to dark mode using CSS variables. The design system ensures:

- **High contrast** for readability
- **Consistent visual hierarchy** in both modes
- **Accessible color combinations** (WCAG AA compliant)

## Color Combinations

### Accessible Combinations

✅ **Good:**
- `bg-primary` + `text-primary-foreground` (white)
- `bg-destructive` + `text-destructive-foreground` (white)
- `bg-background` + `text-foreground`
- `bg-muted` + `text-muted-foreground`

❌ **Avoid:**
- `bg-primary` + `text-primary` (low contrast)
- `bg-accent` + `text-accent` (low contrast)
- Light colors on light backgrounds without proper contrast

## Status Colors

For status indicators, use semantic colors:

| Status | Color | Usage |
|--------|-------|-------|
| Success | `green-500` / `green-600` | Completed, success states |
| Warning | `yellow-500` / `yellow-600` | Warnings, pending states |
| Info | `blue-500` / `blue-600` | Information, in-progress |
| Error | `destructive` | Errors, failed states |

**Examples:**
```tsx
// Success badge
<Badge variant="success">Completed</Badge>

// Warning badge
<Badge variant="warning">Pending</Badge>

// Info badge
<Badge variant="info">In Progress</Badge>
```

## Best Practices

1. **Use semantic tokens**: Always prefer `primary`, `accent`, `destructive` over raw colors
2. **Maintain contrast**: Ensure text is readable on backgrounds (WCAG AA minimum)
3. **Be consistent**: Use the same color for the same semantic meaning
4. **Test dark mode**: Always verify colors work in both light and dark modes
5. **Avoid hardcoded colors**: Use CSS variables for all colors
