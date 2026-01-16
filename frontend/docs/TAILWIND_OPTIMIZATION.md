# Tailwind CSS Optimization Guide

## Overview

This document outlines best practices for using Tailwind CSS in the InTracker frontend, including optimization strategies and common patterns.

## Current Status

- **CSS Bundle Size**: ~41.45 kB (7.64 kB gzipped)
- **Configuration**: Optimized with content paths and future flags
- **Custom Utilities**: Well-organized in `index.css`

## Best Practices

### 1. Use Semantic Colors

Always use semantic color tokens instead of hardcoded colors:

```tsx
// ✅ Good - Semantic colors
<div className="bg-primary text-primary-foreground">
<div className="bg-muted text-muted-foreground">
<div className="bg-destructive text-destructive-foreground">

// ❌ Bad - Hardcoded colors
<div className="bg-green-500 text-white">
<div className="bg-blue-600 text-white">
```

**Why?**
- Automatic dark mode support
- Consistent theming
- Easier to maintain and update

### 2. Use Custom Utility Classes

Leverage custom utility classes defined in `index.css`:

```tsx
// ✅ Good - Custom utilities
<Card className="hover:shadow-soft hover-lift transition-smooth">

// ❌ Bad - Inline classes
<Card className="hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
```

**Available Custom Utilities:**
- `transition-smooth` - Smooth transitions
- `shadow-subtle`, `shadow-soft`, `shadow-elevated` - Consistent shadows
- `hover-lift` - Hover lift effect
- `hover-scale` - Hover scale effect
- `active-scale` - Active scale effect
- `fade-in`, `fade-out` - Fade animations
- `slide-in-from-*` - Slide animations
- `icon-xs`, `icon-sm`, `icon-md`, `icon-lg`, `icon-xl` - Icon sizing

### 3. Responsive Design

Always use mobile-first approach:

```tsx
// ✅ Good - Mobile first
<div className="text-sm md:text-base lg:text-lg">
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">

// ❌ Bad - Desktop first
<div className="text-lg md:text-base sm:text-sm">
```

### 4. Spacing System

Use consistent spacing scale (4px base unit):

```tsx
// Common patterns
<div className="space-y-4">        // 16px vertical spacing
<div className="gap-2">            // 8px gap
<div className="p-6">              // 24px padding (standard for cards)
<div className="px-4 py-2">        // Directional padding
```

**Spacing Scale:**
- `0.5` = 2px (xs) - Tight spacing
- `1` = 4px (sm) - Small spacing
- `2` = 8px (md) - Default spacing
- `3` = 12px (lg) - Medium spacing
- `4` = 16px (xl) - Large spacing
- `6` = 24px (2xl) - Extra large spacing
- `8` = 32px (3xl) - Hero spacing

### 5. Avoid Inline Styles

Prefer Tailwind classes over inline styles:

```tsx
// ✅ Good - Tailwind classes
<div className="p-4 rounded-lg bg-card">

// ⚠️ Acceptable - Dynamic values
<div style={{ paddingLeft: `${depth * 1.5 + 0.5}rem` }}>
  {/* Only for calculated/dynamic values */}
</div>

// ❌ Bad - Static inline styles
<div style={{ padding: '16px', borderRadius: '8px' }}>
```

### 6. Component Composition

Use `cn()` utility for conditional classes:

```tsx
import { cn } from '@/lib/utils'

<div className={cn(
  "base-classes",
  condition && "conditional-classes",
  className // Allow override
)}>
```

### 7. Color Variants

Use semantic color variants for badges and status indicators:

```tsx
// ✅ Good - Semantic variants
<Badge variant="success">  // Uses primary colors
<Badge variant="warning">  // Uses accent colors
<Badge variant="destructive">  // Uses destructive colors

// ❌ Bad - Hardcoded colors
<Badge className="bg-green-500 text-white">
```

## Optimization Strategies

### 1. Content Paths

Tailwind automatically purges unused classes. Ensure all source files are included:

```js
content: [
  "./index.html",
  "./src/**/*.{js,ts,jsx,tsx}",
]
```

### 2. Future Flags

Enable future flags for better optimization:

```js
future: {
  hoverOnlyWhenSupported: true,
}
```

### 3. Custom Utilities

Group related utilities in `@layer utilities` for better organization and potential tree-shaking.

### 4. Avoid Dynamic Class Names

Avoid generating class names dynamically (Tailwind can't detect them):

```tsx
// ❌ Bad - Dynamic class names
<div className={`bg-${color}-500`}>

// ✅ Good - Use variants or conditional classes
<div className={color === 'red' ? 'bg-destructive' : 'bg-primary'}>
```

## Common Patterns

### Cards

```tsx
<Card className="hover:shadow-soft hover-lift transition-smooth">
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    {/* Content */}
  </CardContent>
</Card>
```

### Buttons

```tsx
<Button 
  variant="default" 
  size="default"
  className="focus-ring"
>
  Click me
</Button>
```

### Forms

```tsx
<div className="space-y-2">
  <Label>Email</Label>
  <Input className="focus-ring" />
  <p className="text-sm text-muted-foreground">Helper text</p>
</div>
```

### Status Indicators

```tsx
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="destructive">Error</Badge>
```

## Performance Considerations

1. **Bundle Size**: Current CSS bundle is ~41.45 kB (7.64 kB gzipped), which is excellent
2. **Purge**: Tailwind automatically removes unused classes in production
3. **Custom Utilities**: Reusable utilities reduce duplication
4. **Semantic Colors**: CSS variables enable efficient theming

## Migration Checklist

When refactoring components:

- [ ] Replace hardcoded colors with semantic colors
- [ ] Use custom utility classes where applicable
- [ ] Ensure mobile-first responsive design
- [ ] Use consistent spacing scale
- [ ] Remove inline styles (except for dynamic values)
- [ ] Use `cn()` for conditional classes
- [ ] Test in both light and dark modes

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind CSS Best Practices](https://tailwindcss.com/docs/reusing-styles)
- [Design System Documentation](./COLOR_SYSTEM.md)
- [Spacing System Documentation](./SPACING_SYSTEM.md)
