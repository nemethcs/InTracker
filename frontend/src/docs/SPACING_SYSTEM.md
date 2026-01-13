# Spacing System

Consistent spacing system for InTracker UI components.

## Base Scale

The spacing system uses a 4px base unit (Tailwind's default):

| Size | Value | Pixels | Usage |
|------|-------|--------|-------|
| `0.5` | `xs` | 2px | Tight spacing, inline elements |
| `1` | `sm` | 4px | Small spacing, form fields, badges |
| `2` | `md` | 8px | **Default** - buttons, cards, most UI elements |
| `3` | `lg` | 12px | Medium spacing, sections, lists |
| `4` | `xl` | 16px | Large spacing, containers, groups |
| `6` | `2xl` | 24px | Extra large spacing, page sections |
| `8` | `3xl` | 32px | Hero spacing, major sections |

## Usage Guidelines

### Vertical Spacing (`space-y-*`)

Use for spacing between stacked elements:

```tsx
// Form fields
<div className="space-y-2">
  <Label>Email</Label>
  <Input />
</div>

// Lists
<div className="space-y-3">
  {items.map(item => <Item key={item.id} />)}
</div>

// Page sections
<div className="space-y-6">
  <Section1 />
  <Section2 />
</div>
```

### Horizontal Spacing (`space-x-*`, `gap-*`)

Use for spacing between inline elements:

```tsx
// Button groups
<div className="flex gap-2">
  <Button>Cancel</Button>
  <Button>Save</Button>
</div>

// Inline elements
<div className="flex items-center space-x-2">
  <Icon />
  <Text />
</div>
```

### Padding (`p-*`, `px-*`, `py-*`)

Use for internal spacing within components:

```tsx
// Cards (standard: p-6 = 24px)
<Card className="p-6">
  <Content />
</Card>

// Buttons (standard: px-4 py-2)
<Button className="px-4 py-2">Click</Button>

// Containers
<div className="px-4 sm:px-6 lg:px-8 py-6">
  <Content />
</div>
```

## Common Patterns

### Form Fields
```tsx
<div className="space-y-2">  {/* 8px between label and input */}
  <Label>Email</Label>
  <Input />
</div>
```

### Card Content
```tsx
<Card>
  <CardHeader className="p-6">  {/* 24px padding */}
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent className="p-6 pt-0">  {/* 24px padding, 0 top */}
    <Content />
  </CardContent>
</Card>
```

### Button Groups
```tsx
<div className="flex gap-2">  {/* 8px between buttons */}
  <Button>Cancel</Button>
  <Button>Save</Button>
</div>
```

### Page Sections
```tsx
<div className="space-y-6">  {/* 24px between sections */}
  <Section1 />
  <Section2 />
  <Section3 />
</div>
```

### Lists
```tsx
<div className="space-y-3">  {/* 12px between items */}
  {items.map(item => <Item key={item.id} />)}
</div>
```

## Responsive Spacing

Use responsive variants for different screen sizes:

```tsx
// Responsive padding
<div className="px-4 sm:px-6 lg:px-8">
  <Content />
</div>

// Responsive gaps
<div className="grid gap-4 md:gap-6">
  <Item />
</div>
```

## Best Practices

1. **Be consistent**: Use the same spacing values for similar UI patterns
2. **Use semantic spacing**: `space-y-2` for forms, `space-y-6` for sections
3. **Avoid arbitrary values**: Stick to the scale (0.5, 1, 2, 3, 4, 6, 8)
4. **Consider context**: Tighter spacing for related items, larger for distinct sections
5. **Responsive first**: Use responsive spacing utilities for mobile/desktop differences
