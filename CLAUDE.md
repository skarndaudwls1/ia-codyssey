# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korean-language educational project simulating Mars mission systems. Three independent CLI applications in pure Python (no external dependencies).

## Running Scripts

Each script is a standalone CLI app run directly:

```bash
python week01/main/main.py          # Mission computer log analysis
python week02/Mars/Mars.py          # Flammable material classification
python week02/dom/dom.py            # Mars dome design calculator
```

No build step, no virtual environment required, no external packages.

## Architecture

### Week 1 — Mission Computer Log Analysis (`week01/main/main.py`)
- Reads `mission_computer_main.log` (CSV: timestamp, event, message)
- Pipeline: raw log file → 2D list → sorted list → dict list → JSON
- Manual JSON serialization (no `import json`) — this is intentional per assignment constraints
- Interactive numbered menu in Korean

### Week 2 — Flammable Material Classification (`week02/Mars/Mars.py`)
- Reads `Mars_Base_Inventory_List.csv` (Substance, Weight, Specific Gravity, Strength, Flammability)
- Dangerous items threshold: flammability ≥ 0.7
- Custom binary serialization format (no standard library serializers):
  - 4-byte item count header
  - Per item: field count, then key-value pairs with type tags (`0x00` = string, `0x01` = float)
  - Floats encoded via `float.hex()`
- Outputs: `Mars_Base_Inventory_danger.csv`, `Mars_Base_Inventory_List.bin`

### Week 2 — Dome Design Calculator (`week02/dom/dom.py`)
- Physics: hemisphere surface area = 2πr², weight adjusted for Mars gravity (0.376 × Earth)
- Material DB: Glass, Aluminum, Carbon Steel (hardcoded densities)
- Saves results to `week02/dom/design_dome.py` as text

## Coding Conventions

- All UI strings, comments, and variable names are in Korean
- No external imports — standard library only, and often even standard library serializers (json, pickle, struct) are avoided intentionally to satisfy assignment requirements
- Each week's assignment is self-contained; do not share code across weeks
