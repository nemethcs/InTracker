# Responsive Design Guidelines

Responsive design system for InTracker UI components.

## Breakpoints

Tailwind CSS default breakpoints:

| Breakpoint | Min Width | Usage |
|------------|-----------|-------|
| `sm` | 640px | Small tablets, large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small desktops, laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large desktops |

## Mobile-First Approach

Always design mobile-first, then enhance for larger screens:

```tsx
// ✅ Good - Mobile first
<div className="text-sm md:text-base lg:text-lg">
  Content
</div>

// ❌ Bad - Desktop first
<div className="text-lg md:text-base sm:text-sm">
  Content
</div>
```

## Common Patterns

### Container Padding

```tsx
// Standard container padding
<div className="px-4 sm:px-6 lg:px-8">
  Content
</div>
```

### Responsive Grids

```tsx
// Cards grid - 1 column mobile, 2 tablet, 3 desktop
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  <Card />
  <Card />
  <Card />
</div>
```

### Responsive Typography

```tsx
// Headings - smaller on mobile
<h1 className="text-2xl md:text-3xl lg:text-4xl">
  Title
</h1>

// Body text
<p className="text-sm md:text-base">
  Content
</p>
```

### Responsive Spacing

```tsx
// Tighter spacing on mobile
<div className="space-y-4 md:space-y-6 lg:space-y-8">
  <Section />
</div>

// Responsive padding
<div className="p-4 md:p-6 lg:p-8">
  Content
</div>
```

### Responsive Layouts

```tsx
// Stack on mobile, side-by-side on desktop
<div className="flex flex-col md:flex-row gap-4">
  <div className="flex-1">Left</div>
  <div className="flex-1">Right</div>
</div>
```

### Responsive Navigation

```tsx
// Mobile: hamburger menu, Desktop: sidebar
<Button className="lg:hidden">Menu</Button>
<Sidebar className="hidden lg:block" />
```

### Responsive Tables

```tsx
// Mobile: cards, Desktop: table
<div className="block md:hidden">
  {/* Card view for mobile */}
</div>
<div className="hidden md:block">
  {/* Table view for desktop */}
</div>
```

## Component-Specific Guidelines

### Buttons

```tsx
// Full width on mobile, auto on desktop
<Button className="w-full md:w-auto">
  Action
</Button>

// Icon-only on mobile, with text on desktop
<Button>
  <Icon className="md:mr-2" />
  <span className="hidden md:inline">Text</span>
</Button>
```

### Cards

```tsx
// Responsive padding
<Card className="p-4 md:p-6">
  Content
</Card>
```

### Forms

```tsx
// Stack on mobile, side-by-side on desktop
<div className="space-y-4 md:space-y-0 md:space-x-4 md:flex md:flex-row">
  <Input className="w-full md:w-1/2" />
  <Input className="w-full md:w-1/2" />
</div>
```

### Modals/Dialogs

```tsx
// Full width on mobile, centered on desktop
<DialogContent className="w-full md:w-auto md:max-w-lg">
  Content
</DialogContent>
```

## Best Practices

1. **Mobile-first**: Always start with mobile design, then enhance for larger screens
2. **Test on real devices**: Use browser dev tools and test on actual devices
3. **Touch targets**: Ensure interactive elements are at least 44x44px on mobile
4. **Readable text**: Minimum 16px font size on mobile to prevent auto-zoom
5. **Consistent spacing**: Use responsive spacing utilities consistently
6. **Hide/show patterns**: Use `hidden md:block` for desktop-only elements
7. **Flexible layouts**: Use flexbox/grid with responsive utilities
8. **Image optimization**: Use responsive images with `srcset`

## Testing Checklist

- [ ] Mobile (320px - 640px)
- [ ] Tablet (640px - 1024px)
- [ ] Desktop (1024px+)
- [ ] Large desktop (1280px+)
- [ ] Touch interactions work
- [ ] Text is readable
- [ ] Buttons are tappable
- [ ] Navigation is accessible
- [ ] Forms are usable
- [ ] No horizontal scrolling
