# Accessibility (ARIA Labels and Keyboard Navigation)

## Overview

The frontend application includes comprehensive accessibility features to ensure it's usable by everyone, including users with disabilities who rely on screen readers, keyboard navigation, and other assistive technologies.

## ARIA Labels

### Icon-Only Buttons

All icon-only buttons have descriptive `aria-label` attributes:

```typescript
<Button variant="ghost" size="icon" aria-label="Go back to project">
  <ArrowLeft className={iconSize('sm')} />
</Button>
```

### Navigation Links

Navigation links use `aria-current="page"` to indicate the active page:

```typescript
<Link
  to="/projects"
  aria-current={isActive ? 'page' : undefined}
>
  Projects
</Link>
```

### Icons

Icons that are decorative (not conveying information) use `aria-hidden="true"`:

```typescript
<Icon className="h-5 w-5" aria-hidden="true" />
```

## Keyboard Navigation

### Focus Management

- All interactive elements are keyboard accessible
- Focus indicators are visible with `focus-visible:ring-2` styles
- Tab order follows logical document flow

### Keyboard Shortcuts

Common keyboard shortcuts:

- **Tab**: Navigate forward through interactive elements
- **Shift+Tab**: Navigate backward
- **Enter/Space**: Activate buttons and links
- **Escape**: Close dialogs and modals
- **Arrow Keys**: Navigate within lists and menus (where implemented)

### Focus Trapping

Dialogs and modals trap focus within them when open, preventing users from tabbing to elements outside the modal.

## Form Accessibility

### Labels

All form inputs have associated labels:

```typescript
<FormField label="Name" required>
  <FormInput
    value={name}
    onChange={(e) => setName(e.target.value)}
    placeholder="Enter name"
  />
</FormField>
```

### Required Fields

Required fields are marked with `required` prop and visual indicators (asterisk).

### Error Messages

Form validation errors are associated with inputs using `aria-describedby`:

```typescript
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? 'error-message-id' : undefined}
/>
```

## Dialog and Modal Accessibility

Radix UI components (Dialog, DropdownMenu, etc.) automatically include:

- `role="dialog"` or appropriate ARIA roles
- `aria-labelledby` pointing to the title
- `aria-describedby` pointing to the description
- Focus management
- Escape key handling

## Current Implementation

### Components with ARIA Labels

1. **Header**:
   - Menu toggle button: `aria-label="Open menu"` / `aria-label="Close menu"`
   - Notifications button: `aria-label="Notifications"`
   - User menu: Accessible via Radix UI DropdownMenu

2. **Sidebar**:
   - Close button: `aria-label="Close menu"`
   - Navigation links: `aria-current="page"` for active page
   - Icons: `aria-hidden="true"` for decorative icons

3. **Feature Header**:
   - Back button: `aria-label="Go back to project"`

4. **Settings**:
   - Copy button: `aria-label="Copy MCP key"` / `aria-label="MCP key copied"`

5. **Admin**:
   - Delete user button: `aria-label="Delete user {email}"`

6. **Teams**:
   - Remove member button: `aria-label="Remove member {name} from team"`

7. **Elements**:
   - View feature button: `aria-label="View feature for todo: {title}"`

## Accessibility Utilities

The `utils/accessibility.ts` file provides:

- `ariaLabels`: Common ARIA label generators
- `keyboardHandlers`: Keyboard event handlers for common actions
- `makeAccessible`: Utility to add ARIA attributes to elements

## Best Practices

1. **Always provide ARIA labels for icon-only buttons**
2. **Use semantic HTML** (buttons for actions, links for navigation)
3. **Ensure keyboard navigation works** for all interactive elements
4. **Provide focus indicators** for keyboard users
5. **Test with screen readers** (VoiceOver, NVDA, JAWS)
6. **Test keyboard-only navigation** (no mouse)
7. **Use proper heading hierarchy** (h1 → h2 → h3)
8. **Provide alt text for images** that convey information
9. **Mark decorative images** with `aria-hidden="true"`
10. **Associate labels with form inputs** using `htmlFor` or wrapping

## Testing

### Manual Testing

1. **Keyboard Navigation**:
   - Tab through all interactive elements
   - Ensure focus is visible
   - Verify logical tab order

2. **Screen Reader Testing**:
   - Test with VoiceOver (macOS/iOS)
   - Test with NVDA (Windows)
   - Verify all interactive elements are announced

3. **Color Contrast**:
   - Ensure text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)

### Automated Testing

Consider adding automated accessibility testing:

- **axe-core**: Browser extension and testing library
- **Lighthouse**: Includes accessibility audit
- **Pa11y**: Command-line accessibility testing

## WCAG Compliance

The application aims to meet **WCAG 2.1 Level AA** standards:

- ✅ Perceivable: Text alternatives, captions, sufficient contrast
- ✅ Operable: Keyboard accessible, no seizure-inducing content
- ✅ Understandable: Readable, predictable, input assistance
- ✅ Robust: Compatible with assistive technologies

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Accessibility Resources](https://webaim.org/)
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
