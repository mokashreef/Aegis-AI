# 🧩 Aegis AI Community Plugins Architecture

This directory (`storage/plugins/`) hosts custom, community-authored modular extensions and Python tools for Aegis AI.

## Directory Structure

```text
storage/plugins/
├── weather_forecast/
│   ├── plugin.yaml       # Standard extension manifest
│   ├── handler.py        # Python tool execution logic
│   └── README.md         # Documentation
└── your_custom_plugin/
    ├── plugin.yaml
    └── main.py
```

## `plugin.yaml` Specification

Each plugin directory must contain a `plugin.yaml` (or `plugin.json`):

```yaml
name: my_custom_tool
version: "1.0.0"
author: "Author Name"
description: "Description of what this plugin provides"
license: "MIT"
tools:
  - name: calculate_sum
    description: "Calculates the sum of two integers"
    risk_level: "read_only"      # Options: read_only, mutating_safe, restricted_confirm
    entrypoint: "handler.py:sum" # Format: filename.py:function_name
    timeout_seconds: 15.0
    parameters:
      type: object
      properties:
        a:
          type: number
        b:
          type: number
      required:
        - a
        - b
```

## Security & Sandboxing Policies
1. **Path Traversal Protection**: Arguments containing relative navigation (`../` or `..\`) are automatically intercepted.
2. **Execution Timeout**: Individual tool calls default to a 15-second timeout to prevent blocking the system.
3. **Safety Confirmation**: Tools marked with `risk_level: restricted_confirm` mandate explicit human authorization before executing.
