# Tailwind CSS v4 + Shadcn UI Configuration

## Overview
This project uses **Tailwind CSS v4** with **Shadcn UI** components. The configuration follows the latest best practices for compatibility and optimal performance.

## Key Changes from Tailwind v3 to v4

### 1. No Configuration File Required
- **Tailwind v4** eliminates the need for `tailwind.config.js` or `tailwind.config.ts`
- All configuration is done directly in CSS using `@theme` and `@theme inline` directives
- The `components.json` file now has an empty string for the `config` field

### 2. PostCSS Plugin Update
- Use `@tailwindcss/postcss` instead of `tailwindcss` package
- No need for `postcss-import` or `autoprefixer` (handled automatically)

```javascript
// postcss.config.mjs
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
export default config;
```

### 3. CSS Import Syntax
- Use `@import "tailwindcss"` instead of separate base/components/utilities imports
- This single import handles all Tailwind functionality

### 4. Color Format: OKLCH
- Shadcn UI now uses **OKLCH color format** for better color accuracy and perceptual uniformity
- OKLCH provides more predictable color manipulation compared to HSL
- Format: `oklch(lightness chroma hue)`
  - Lightness: 0 (black) to 1 (white)
  - Chroma: 0 (gray) to ~0.4 (vibrant)
  - Hue: 0-360 degrees

### 5. Theme Variable Mapping
Two-layer approach for dynamic theming:

#### Layer 1: Dynamic CSS Variables (`:root` and `.dark`)
```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  /* ... other colors */
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  /* ... other colors */
}
```

#### Layer 2: Tailwind Theme Mapping (`@theme inline`)
```css
@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  /* Maps CSS variables to Tailwind utilities */
}
```

**Why this approach?**
- CSS variables in `:root` can be dynamically changed with JavaScript
- `@theme inline` maps these to Tailwind's utility classes (e.g., `bg-background`, `text-foreground`)
- Allows runtime theme switching without regenerating CSS

### 6. Custom Dark Variant
```css
@custom-variant dark (&:is(.dark *));
```
This defines how the `dark:` modifier works in Tailwind v4, targeting elements inside a `.dark` class.

### 7. Base Layer Styles
```css
@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```
Sets default border and outline colors, plus body background/text colors.

## File Structure

### `/frontend/postcss.config.mjs`
PostCSS configuration using the new `@tailwindcss/postcss` plugin.

### `/frontend/app/globals.css`
Contains:
- `@import "tailwindcss"` - Main Tailwind import
- `@custom-variant dark` - Custom dark mode variant
- `:root` - Light theme CSS variables (OKLCH format)
- `.dark` - Dark theme CSS variables (OKLCH format)
- `@theme inline` - Maps CSS variables to Tailwind utilities
- `@layer base` - Base styles for all elements
- Custom component styles (scrollbars, BlockNote, etc.)

### `/frontend/components.json`
Shadcn UI configuration:
```json
{
  "tailwind": {
    "config": "",  // Empty for v4 - no config file needed
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true  // Use CSS variables for theming
  }
}
```

## Shadcn UI Component Integration

### Radius Utilities
Automatically generated from `--radius` variable:
- `--radius-sm: calc(var(--radius) - 4px)`
- `--radius-md: calc(var(--radius) - 2px)`
- `--radius-lg: var(--radius)`
- `--radius-xl: calc(var(--radius) + 4px)`

Use in components: `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`

### Color Utilities
All Shadcn colors are available as utilities:
- Background: `bg-background`, `bg-card`, `bg-popover`
- Text: `text-foreground`, `text-muted-foreground`
- Borders: `border-border`, `border-input`
- Interactive: `bg-primary`, `bg-secondary`, `bg-accent`, `bg-destructive`
- Rings: `ring-ring`

### Chart Colors
- `--chart-1` through `--chart-5` for consistent data visualization colors

### Sidebar Colors
- `--sidebar`, `--sidebar-foreground`, `--sidebar-primary`, etc.
- Used for sidebar components with `bg-sidebar`, `text-sidebar-foreground`, etc.

## Custom Variables

### Layout Variables
```css
:root {
  --sidebar-width-expanded: 16rem;
  --sidebar-width-collapsed: 4rem;
  --transition-duration: 300ms;
}
```

These are **not** mapped to `@theme inline` because they're used directly in CSS:
```css
.sidebar-transition {
  transition: width var(--transition-duration) ease-in-out;
}
```

## Migration Notes

### Size Utilities (v3.4+)
Replace separate width and height classes with `size-*`:
```diff
- w-4 h-4
+ size-4
```

### No `theme()` Function in CSS
Instead of `theme('colors.red.500')`, use CSS variables:
```css
/* Old (v3) */
color: theme('colors.red.500');

/* New (v4) */
color: var(--color-red-500);
```

### Media Queries
For media queries that need theme values, use CSS variable names:
```css
@media (width >= theme(--breakpoint-xl)) {
  /* ... */
}
```

## Benefits of This Setup

1. **No Build Configuration**: All theme config in CSS
2. **Dynamic Theming**: CSS variables can be changed at runtime
3. **Better Color Space**: OKLCH provides perceptually uniform colors
4. **Smaller Bundle**: No config parsing at build time
5. **Framework Agnostic**: Works with React, Vue, Svelte, etc.
6. **Future Proof**: Aligned with Tailwind v4 and Shadcn UI latest practices

## Testing the Configuration

To verify everything is working:

1. **Build the project**:
   ```bash
   npm run build
   ```

2. **Check for errors** in the terminal output

3. **Verify theme colors** are applied correctly in the browser

4. **Test dark mode** by adding `className="dark"` to a parent element

5. **Inspect CSS variables** in browser DevTools:
   - Should see `--background`, `--foreground`, etc. in `:root`
   - Should see `--color-background`, `--color-foreground`, etc. mapped by Tailwind

## Troubleshooting

### Colors Not Working
- Ensure `@import "tailwindcss"` is at the top of `globals.css`
- Check that `@theme inline` block maps all required colors
- Verify PostCSS is using `@tailwindcss/postcss` plugin

### Dark Mode Not Working
- Ensure `@custom-variant dark` is defined
- Check that `.dark` class is applied to a parent element
- Verify dark mode variables are defined in `.dark` selector

### Build Errors
- Remove any old `tailwind.config.js` or `tailwind.config.ts` files
- Ensure `components.json` has empty string for `tailwind.config`
- Update `@tailwindcss/postcss` to latest v4 version

## References

- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [Tailwind CSS v4 Upgrade Guide](https://tailwindcss.com/docs/upgrade-guide)
- [Shadcn UI Documentation](https://ui.shadcn.com)
- [Shadcn UI Tailwind v4 Guide](https://ui.shadcn.com/docs/tailwind-v4)
- [OKLCH Color Format](https://evilmartians.com/chronicles/oklch-in-css-why-quit-rgb-hsl)
