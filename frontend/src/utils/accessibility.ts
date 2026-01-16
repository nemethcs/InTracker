/**
 * Accessibility utilities for ARIA labels and keyboard navigation
 */

/**
 * Generate ARIA label for icon-only buttons
 */
export function getIconButtonAriaLabel(action: string, item?: string): string {
  if (item) {
    return `${action} ${item}`
  }
  return action
}

/**
 * Common ARIA labels for actions
 */
export const ariaLabels = {
  edit: (item: string) => `Edit ${item}`,
  delete: (item: string) => `Delete ${item}`,
  close: () => 'Close',
  open: (item: string) => `Open ${item}`,
  save: () => 'Save',
  cancel: () => 'Cancel',
  back: () => 'Go back',
  next: () => 'Next',
  previous: () => 'Previous',
  search: () => 'Search',
  filter: () => 'Filter',
  sort: () => 'Sort',
  refresh: () => 'Refresh',
  add: (item: string) => `Add ${item}`,
  remove: (item: string) => `Remove ${item}`,
  view: (item: string) => `View ${item}`,
  expand: () => 'Expand',
  collapse: () => 'Collapse',
  menu: () => 'Menu',
  settings: () => 'Settings',
  notifications: () => 'Notifications',
  profile: () => 'Profile',
  logout: () => 'Logout',
}

/**
 * Keyboard event handlers for common actions
 */
export const keyboardHandlers = {
  /**
   * Handle Enter key press
   */
  onEnter: (handler: () => void) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handler()
    }
  },

  /**
   * Handle Escape key press
   */
  onEscape: (handler: () => void) => (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      handler()
    }
  },

  /**
   * Handle Arrow keys for navigation
   */
  onArrowKeys: (
    onUp?: () => void,
    onDown?: () => void,
    onLeft?: () => void,
    onRight?: () => void
  ) => (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault()
        onUp?.()
        break
      case 'ArrowDown':
        e.preventDefault()
        onDown?.()
        break
      case 'ArrowLeft':
        e.preventDefault()
        onLeft?.()
        break
      case 'ArrowRight':
        e.preventDefault()
        onRight?.()
        break
    }
  },
}

/**
 * Make an element focusable and keyboard accessible
 */
export function makeAccessible(
  element: HTMLElement,
  options: {
    tabIndex?: number
    role?: string
    ariaLabel?: string
    ariaExpanded?: boolean
    ariaControls?: string
  } = {}
) {
  if (options.tabIndex !== undefined) {
    element.tabIndex = options.tabIndex
  }
  if (options.role) {
    element.setAttribute('role', options.role)
  }
  if (options.ariaLabel) {
    element.setAttribute('aria-label', options.ariaLabel)
  }
  if (options.ariaExpanded !== undefined) {
    element.setAttribute('aria-expanded', String(options.ariaExpanded))
  }
  if (options.ariaControls) {
    element.setAttribute('aria-controls', options.ariaControls)
  }
}
