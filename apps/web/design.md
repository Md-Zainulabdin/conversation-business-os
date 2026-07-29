# DESIGN.md — Attio-Style CRM Design System & Guidelines (Shadcn UI Architecture)

## 1. Design Philosophy & Core Principles

Building a modern CRM like Attio requires balancing **high data density** with **quiet sophistication**. The interface must feel fast, relational, highly customizable, and focused.

### Core Pillars
1. **Relational Clarity:** Data is interconnected (People, Companies, Deals, Workspaces). Views must clearly communicate relationships through high-contrast badges, visual linkages, and inline drawers.
2. **Keyboard-First Motion:** Power users operate at high speed. Every primary action (searching, filtering, updating records, switching views) must be accessible via global command palettes (`Cmd + K`) and contextual hotkeys.
3. **Quiet Sophistication & Surface Depth:** Minimize heavy drop shadows and loud background colors. Rely on 1px precision borders (`border-border`), subtle background layers, and strategic accent pops.
4. **View-Centric Flexibility:** The canvas transforms seamlessly between Spreadsheet Grids, Kanban Boards, Lists, and Timelines. Components must adapt to dense row states without layout shifts.
5. **Shadcn Composability:** Every UI element is built upon modular, accessible primitives (Radix UI) styled with Tailwind CSS, ensuring complete source-code ownership and zero lock-in.

---

## 2. Design Tokens & Theme Configuration

### 2.1 CSS Variables (`globals.css`)

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 220 13% 13%;

    --card: 0 0% 100%;
    --card-foreground: 220 13% 13%;
    --popover: 0 0% 100%;
    --popover-foreground: 220 13% 13%;

    --primary: 217 87% 55%;
    --primary-foreground: 0 0% 100%;

    --secondary: 220 14% 96%;
    --secondary-foreground: 220 13% 13%;
    --muted: 220 14% 96%;
    --muted-foreground: 220 9% 46%;

    --accent: 217 87% 94%;
    --accent-foreground: 217 87% 40%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;

    --border: 220 13% 91%;
    --input: 220 13% 91%;
    --ring: 217 87% 55%;

    --radius: 0.375rem;
  }

  .dark {
    --background: 220 13% 6%;
    --foreground: 210 20% 96%;

    --card: 220 13% 8%;
    --card-foreground: 210 20% 96%;
    --popover: 220 13% 8%;
    --popover-foreground: 210 20% 96%;

    --primary: 217 87% 55%;
    --primary-foreground: 0 0% 100%;

    --secondary: 217 19% 15%;
    --secondary-foreground: 210 20% 96%;
    --muted: 217 19% 15%;
    --muted-foreground: 215 13% 65%;

    --accent: 217 87% 15%;
    --accent-foreground: 217 87% 80%;
    --destructive: 0 62% 30%;
    --destructive-foreground: 210 20% 96%;

    --border: 217 19% 16%;
    --input: 217 19% 16%;
    --ring: 217 87% 55%;
  }
}
```

### 2.2 Functional Accent Palette

| Functional Role | Color Name | Hex Code | Tailwind Usage |
| --- | --- | --- | --- |
| **Primary Identifier** | Cobalt Blue | `#266DF0` | `bg-primary` / `text-primary` |
| **Success / Active** | Emerald Green | `#10B981` | `bg-emerald-500` |
| **Pipeline / In Progress** | Electric Amber | `#F59E0B` | `bg-amber-500` |
| **High Priority / Risk** | Soft Coral | `#F43F5E` | `bg-rose-500` |

---

## 3. Typography & Micro-Scales

Font: **Inter** (via `next/font`)

```
Display Large:   24px / Lh: 1.2 / Wt: 600 (-0.02em)  -> Section / Workspace Headers
Heading Medium:  18px / Lh: 1.3 / Wt: 600 (-0.01em)  -> Drawer Record Titles
Body Regular:    14px / Lh: 1.5 / Wt: 400 (0em)      -> Table Cells, Form Inputs
Body Compact:    13px / Lh: 1.4 / Wt: 400 (0em)      -> Dense Table Cells, Sidebar Items
Caption / Meta:  12px / Lh: 1.3 / Wt: 500 (+0.01em)  -> Metadata Badges, Helper Text
Micro Tag:       11px / Lh: 1.0 / Wt: 600 (+0.03em)  -> UPPERCASE Table Headers & Status Tags
```

### Label Rules
- **Metadata & Column Headers:** 11px UPPERCASE (`tracking-wider text-muted-foreground font-semibold`)
- **Attribute Badges:** Pills at 12px medium weight with `rounded-md`

---

## 4. Spatial System & Layout Architecture

```
+-------------------------------------------+
| GLOBAL TOP HEADER (h-12)                  |
+--------------+----------------------------+
| LEFT NAV     | MAIN CANVAS (Flex-1)       |
| (w-60)       |                            |
| Collapsible  | High-Density Grid / Table   |
|              |                            |
+--------------+----------------------------+
```

### Key Spatial Metrics
- **Top Bar Height:** `48px` (`h-12`)
- **Left Navigation Width:** `240px` (`w-60`)
- **Table Row Density:** `h-10` (default)
- **Corner Radius:**
  - Containers & Modals: `rounded-lg` (8px)
  - Buttons & Inputs: `rounded-md` (6px)
  - Status Pills & Badges: `rounded-md` (4-6px)

---

## 5. Shadcn Component Mapping

| CRM Pattern | Shadcn Component |
| --- | --- |
| Data Table / Grid | `<Table />` |
| Command Palette / Search | `<Command />` |
| Record Inspector | `<Sheet />` |
| View Selector | `<Tabs />`, `<Popover />` |
| Filter Builder | `<Popover />`, `<Select />` |
| Status Tags | `<Badge />` |
| Form Controls | `<Form />`, `<Input />`, `<Textarea />` |
| Dialogs | `<Dialog />` |

### Data Table Styling
- **Borders:** 1px grid lines (`border-border`)
- **Header:** Sticky, `bg-muted/40`, 11px uppercase text
- **Row Hover:** `hover:bg-muted/50 transition-colors`

---

## 6. Micro-Interactions

- **Hover Transitions:** `transition-all duration-150 ease-out`
- **Modal / Drawer Slide:** `duration-200 cubic-bezier(0.16, 1, 0.3, 1)`
- **Skeleton Loaders:** Use `<Skeleton />` during data fetching
- **Zero States:** Clean icon container + clear CTA button

---

## 7. Accessibility (WCAG 2.1 AA)

- **Contrast:** Text must meet 4.5:1 against backgrounds
- **Keyboard:** `<Sheet />` and `<Dialog />` trap focus, dismiss via Escape
- **ARIA:** Interactive tables use `role="grid"`, `role="row"`, `role="gridcell"`

---

## 8. Design Checklist

- [ ] Data Density: vertical padding compact (`h-10` rows)
- [ ] Border System: 1px `border-border` separators
- [ ] Theme Variables: colors from HSL tokens
- [ ] Metadata Formatting: 11px UPPERCASE headers
- [ ] Keyboard Accessibility: primary actions via keyboard
- [ ] Dark Mode: crisp without overwhelming contrast
- [ ] Smooth hover states (150ms) without layout reflow
