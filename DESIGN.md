---
name: DDNS Signal Workbench
description: A restrained signal-path workbench for operating and configuring a local DDNS client.
colors:
  route-cobalt: "#0a73c5"
  route-cobalt-hover: "#075c9f"
  route-cobalt-soft: "#e2f0fb"
  cool-canvas: "#e9eef2"
  paper-surface: "#fcfdfd"
  muted-surface: "#f2f5f7"
  strong-surface: "#e6ecef"
  graphite-ink: "#10212c"
  graphite-soft: "#314753"
  slate-muted: "#5b6e79"
  slate-faint: "#778993"
  rule-line: "#cdd7dd"
  rule-line-strong: "#9babb4"
  healthy-green: "#087a56"
  caution-amber: "#9a5a0a"
  failure-red: "#b22f46"
  instrument-navy: "#08151e"
  instrument-raised: "#0d1d28"
  instrument-line: "#29404d"
  instrument-text: "#eff6f8"
  instrument-muted: "#9fb0b9"
  instrument-blue: "#39a0ff"
  instrument-green: "#4fd0a0"
  instrument-amber: "#f0b35b"
  action-ink: "#0b2838"
  instrument-border: "#36505f"
  status-slate: "#5b7481"
  status-violet: "#7454c6"
  status-ochre: "#83591f"
  status-rose: "#8c3344"
  status-violet-light: "#b7a0ff"
  status-rose-light: "#ffadb9"
  shadow-black-20: "rgba(0, 0, 0, 0.2)"
  shadow-panel-07: "rgba(24, 48, 61, 0.07)"
  shadow-panel-08: "rgba(24, 48, 61, 0.08)"
  shadow-panel-09: "rgba(24, 48, 61, 0.09)"
  night-canvas: "#071018"
  night-surface: "#0f1a23"
  night-surface-muted: "#13212c"
  night-ink: "#edf4f7"
  night-line: "#273b47"
  night-accent: "#55adf4"
typography:
  metric:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "27px"
    fontWeight: 620
    lineHeight: 1.2
    letterSpacing: "normal"
  headline:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  setup:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "23px"
    fontWeight: 710
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  title:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "22px"
    fontWeight: 720
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  mobile-headline:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "21px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  mobile-title:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "20px"
    fontWeight: 720
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  compact-heading:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "19px"
    fontWeight: 690
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  compact-title:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  control:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "13px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "normal"
  metadata:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "12px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "normal"
  label:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "11px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "normal"
  caption:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "10px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "normal"
  micro:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, PingFang SC, Microsoft YaHei, sans-serif"
    fontSize: "9px"
    fontWeight: 760
    lineHeight: 1.3
    letterSpacing: "normal"
  mono:
    fontFamily: "SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
rounded:
  trace: "2px"
  micro: "3px"
  tag: "4px"
  field: "5px"
  control: "6px"
  brand: "7px"
  icon: "8px"
  compact-panel: "9px"
  panel: "10px"
  instrument: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "14px"
  lg: "20px"
  xl: "28px"
  xxl: "38px"
components:
  button-primary:
    backgroundColor: "{colors.route-cobalt}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.route-cobalt-hover}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.paper-surface}"
    textColor: "{colors.graphite-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "38px"
  input:
    backgroundColor: "{colors.paper-surface}"
    textColor: "{colors.graphite-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "0 11px"
    height: "40px"
  settings-panel:
    backgroundColor: "{colors.paper-surface}"
    textColor: "{colors.graphite-ink}"
    rounded: "{rounded.panel}"
  signal-deck:
    backgroundColor: "{colors.instrument-navy}"
    textColor: "{colors.instrument-text}"
    rounded: "{rounded.instrument}"
---

# Design System: DDNS Signal Workbench

## Overview

**Creative North Star: "Signal Path Workbench / 信号路径工作台"**

Signal Path Workbench treats DDNS as a live route to inspect rather than a generic administration portal. Cool powder-coated surfaces form the workbench; one dark instrument deck carries the operational conclusion and traces local address through DNS provider to records. The interface is quiet enough for daily use but precise enough to diagnose a failure at a glance.

The system feels engineered, local, and trustworthy. It uses restrained density, ruled calibration forms, explicit state language, and a single cobalt action path. Configuration remains part of the same workbench, while complex design tooling stays outside the built-in console.

**Key Characteristics:**
- Operational state leads; configuration detail follows.
- One dark signal deck anchors an otherwise light, cool-gray workspace.
- Cobalt indicates routes and explicit actions; semantic colors report state only.
- Rules, alignment, and compact labels create structure without a sidebar or card wall.
- First-run replaces unavailable runtime content with the real configuration editor.

## Colors

The palette pairs cool industrial neutrals with one route cobalt and tightly controlled semantic signals.

### Primary
- **Route Cobalt** (`#0a73c5`): Primary actions, active navigation, focused fields, and the visible DDNS route.
- **Deep Route Cobalt** (`#075c9f`): Hovered primary actions where stronger contrast confirms intent.
- **Soft Route Wash** (`#e2f0fb`): Low-emphasis selected or informational backgrounds.

### Tertiary
- **Healthy Green** (`#087a56`): Successful synchronization and available runtime state.
- **Caution Amber** (`#9a5a0a`): Unsaved, not-yet-configured, and attention states.
- **Failure Red** (`#b22f46`): Invalid configuration, connection failure, and destructive actions.

### Neutral
- **Cool Canvas** (`#e9eef2`): The powder-coated page ground.
- **Paper Surface** (`#fcfdfd`): Forms, ledgers, and settings groups.
- **Graphite Ink** (`#10212c`): Primary text and operational labels.
- **Slate Muted** (`#5b6e79`): Explanations, metadata, and secondary controls.
- **Rule Line** (`#cdd7dd`): Structural separators and field borders.
- **Instrument Navy** (`#08151e`): The runtime signal deck.
- **Instrument Text** (`#eff6f8`): High-contrast conclusions inside the signal deck.

**The Signal Economy Rule.** Cobalt is reserved for the active route and explicit actions; green, amber, and red report state and never become decoration.

## Typography

**Display Font:** System UI sans-serif (`Segoe UI`, `PingFang SC`, `Microsoft YaHei`, sans-serif)
**Body Font:** System UI sans-serif (`Segoe UI`, `PingFang SC`, `Microsoft YaHei`, sans-serif)
**Label/Mono Font:** `SFMono-Regular`, Consolas, `Liberation Mono`, monospace for addresses, paths, and machine values

**Character:** Native system typography keeps the embedded console fast and legible across platforms. Weight and spacing, rather than a decorative typeface, distinguish operational conclusions from compact machine metadata.

### Hierarchy
- **Metric** (620, 27px, 1.2): Address, provider, and record counts along the signal path.
- **Headline** (700, 25px, 1.2): The current runtime conclusion inside the instrument deck.
- **Setup** (710, 23px, 1.2): First-run orientation and major setup guidance.
- **Title** (720, 22px, 1.2): Page and configuration section headings.
- **Responsive Headings** (690-720, 18-21px, 1.2): Compact equivalents used only as the viewport narrows.
- **Body** (400, 14px, 1.5): Form values and general interface copy, with explanations capped near 66-72 characters.
- **Control / Metadata** (650, 12-13px, 1.4): Buttons, navigation, status values, and secondary row content.
- **Label** (650, 11px, 1.4): Field labels, status captions, and ledger metadata.
- **Caption / Micro** (500-760, 9-10px, 1.3-1.4): Dense badges and machine annotations that are never the sole carrier of a critical instruction.

**The Measurement Label Rule.** Machine values may use monospace, but headings and action labels remain in the system sans-serif so the console reads as a product, not a terminal.

## Layout

The workbench uses a centered container capped at 1240px with 20px viewport gutters and a 62px sticky command header. Configured state opens with the operational conclusion, then uses paired ruled ledgers for addresses, providers, records, and activity. Configuration is a continuous form surface rather than a stack of independent cards.

At 1040px and 800px, paired data regions collapse progressively. At 720px, the signal path turns vertical, page padding tightens, actions wrap, and form columns become one column. At 480px, the header and configuration tools compress again without hiding primary actions.

**The State Before Settings Rule.** When configuration exists, the first viewport answers whether DDNS is healthy; when it does not, the real configuration editor becomes the first viewport and unavailable runtime navigation is disabled.

## Elevation & Depth

Depth is mostly tonal and structural: canvas, paper, ruled borders, and the dark instrument deck establish hierarchy before shadows do. Soft ambient shadows appear only under the sticky brand mark, primary actions, major panels, and the signal deck; they never turn every region into a floating card.

### Shadow Vocabulary
- **Instrument Lift** (`0 16px 34px rgba(15, 36, 48, 0.16)`): Separates the signal deck from the workbench.
- **Panel Lift** (`0 8px 20px rgba(24, 48, 61, 0.07)`): Gives major grouped surfaces a low ambient edge.
- **Action Lift** (`0 6px 14px rgba(7, 92, 159, 0.18)`): Confirms the primary save action.
- **Focus Ring** (`0 0 0 3px rgba(10, 115, 197, 0.11)`): Makes keyboard and field focus visible without changing layout.

**The One Pulse Rule.** The address-to-provider-to-record route is the only continuously expressive motion, and it runs only while synchronization is active.

## Shapes

The form language is compact and engineered: 2-4px trace and badge details, 5px fields, 6-7px controls and brand marks, 8-9px compact housings, 10px grouped surfaces, and a 12px signal deck. Thin one-pixel rules connect related values and divide ledgers. Circular forms are reserved for state lamps, route nodes, and numbered first-run steps.

**The Ruled Surface Rule.** Prefer one continuous surface divided by lines over collections of unrelated rounded cards.

## Components

### Buttons
- **Shape:** Compact rectangular controls with a 6px radius and a 38px minimum height.
- **Primary:** Route cobalt with white text, 14px horizontal padding, and a restrained action shadow.
- **Hover / Focus:** Deepen the cobalt on hover; use the shared three-pixel cobalt focus outline.
- **Secondary / Ghost:** Paper with a rule-line border for secondary actions; transparent and muted for low-priority tools.

### Chips
- **Style:** Status lamps and compact labels use semantic foreground colors with soft tonal backgrounds.
- **State:** Green means healthy, amber means incomplete or attention, and red means invalid or failed.

### Cards / Containers
- **Corner Style:** 10px for settings groups and 12px for the signal deck.
- **Background:** Paper surfaces on the cool canvas; instrument navy only for the operational conclusion.
- **Shadow Strategy:** Use the ambient vocabulary above only on major grouped surfaces.
- **Border:** One-pixel rule lines provide most internal structure.
- **Internal Padding:** Generally 20-30px on desktop and 14-20px on mobile.

### Inputs / Fields
- **Style:** Paper background, one-pixel rule-line stroke, 5px radius, and a 40px control height.
- **Focus:** Route-cobalt border plus a soft three-pixel focus ring.
- **Error / Disabled:** Semantic error messaging remains adjacent; disabled controls use reduced opacity and a not-allowed cursor.

### Navigation
- **Style:** A centered two-command header with compact 13px labels. Active state uses graphite text and a two-pixel cobalt baseline; unavailable routes become visibly muted and non-interactive.
- **Mobile:** Preserve both commands and the status indicator; remove secondary brand copy before reducing action clarity.

### Signal Path Deck

The signature instrument surface combines the current conclusion, an explicit sync action, a three-station route, and the latest operational evidence. It is the only dark major surface and the only place where synchronization animates along a path.

### Calibration Form

Configuration uses a continuous ruled editor. Service credentials, A/AAAA domains, network policy, and automation are separated by headers and dividers while preserving one shared save state and one explicit write action.

## Do's and Don'ts

### Do:
- **Do** keep the current operational state and next safe action visible before configuration detail.
- **Do** use real local runtime data, explicit empty states, and reversible configuration language.
- **Do** preserve the 2-12px radius ladder and ruled internal alignment across new controls.
- **Do** make network-changing actions explicit and show their resulting local state.
- **Do** collapse grids and the signal route deliberately at the 1040px, 800px, 720px, and 480px breakpoints.

### Don't:
- **Don't** introduce a sidebar, dashboard card wall, decorative gradients, or ornamental grid backgrounds.
- **Don't** use semantic green, amber, or red as general brand color.
- **Don't** duplicate the documentation Config Studio inside the embedded console.
- **Don't** expand inherited defaults into the saved configuration merely to fill the form.
- **Don't** fabricate monitoring history, provider health, or synchronization evidence.
