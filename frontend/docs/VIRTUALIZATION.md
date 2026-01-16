# List Virtualization

## Overview

List virtualization is implemented to improve performance when rendering large lists. Instead of rendering all items at once, only visible items are rendered, significantly reducing DOM nodes and improving scroll performance.

## Implementation

### VirtualizedGrid Component

A reusable `VirtualizedGrid` component (`frontend/src/components/ui/VirtualizedGrid.tsx`) provides virtualization for grid layouts.

**Features:**
- Only renders visible rows
- Supports responsive column counts (function-based)
- Configurable item height and gap
- Overscan for smoother scrolling
- TypeScript support with generics

**Usage:**
```tsx
<VirtualizedGrid
  items={items}
  columns={(width) => {
    if (width >= 1024) return 3
    if (width >= 768) return 2
    return 1
  }}
  gap={16}
  itemHeight={180}
  renderItem={(item) => <ItemCard item={item} />}
  containerClassName="h-full"
/>
```

### When to Use Virtualization

Virtualization is automatically applied when:
- **Todos list**: More than 20 todos
- **Ideas list**: More than 20 ideas
- **Projects list (Dashboard)**: More than 20 projects per team

For smaller lists, the standard grid layout is used to avoid virtualization overhead.

## Implemented Pages

### 1. Todos Page (`frontend/src/pages/Todos.tsx`)
- Virtualizes todo cards in a responsive grid
- Columns: 3 (lg), 2 (md), 1 (sm)
- Item height: 180px

### 2. Ideas Page (`frontend/src/pages/Ideas.tsx`)
- Virtualizes idea cards in a responsive grid
- Columns: 3 (lg), 2 (md), 1 (sm)
- Item height: 220px

### 3. Dashboard (`frontend/src/pages/Dashboard.tsx`)
- Virtualizes project cards per team
- Columns: 4 (xl), 3 (lg), 2 (md), 1 (sm)
- Item height: 240px

## Technical Details

### Library

We use `@tanstack/react-virtual` for virtualization, which:
- Provides efficient virtual scrolling
- Supports both horizontal and vertical scrolling
- Handles dynamic item sizes
- Works well with React Query (already in use)

### Responsive Columns

The `columns` prop can be either:
- A number: Static column count
- A function: Dynamic column count based on window width

```tsx
// Static
columns={3}

// Dynamic
columns={(width) => {
  if (width >= 1024) return 3
  if (width >= 768) return 2
  return 1
}}
```

### Performance Benefits

- **Reduced DOM nodes**: Only visible items are rendered
- **Faster initial load**: Less work on first render
- **Smoother scrolling**: Fewer elements to update
- **Lower memory usage**: Only visible items in memory

### Future Improvements

1. **Virtualized Table**: For tabular data (e.g., GitHub repositories)
2. **Horizontal Virtualization**: For wide lists
3. **Dynamic Item Heights**: Support for variable-height items
4. **Infinite Scroll**: Combine with pagination for very large datasets
