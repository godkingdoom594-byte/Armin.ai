#!/usr/bin/env python3
"""
Simple CLI config generator:
- Reads a JSON Schema file (--schema)
- Prompts the user for each property (supports string/number/integer/boolean/enum)
- Validates the result with jsonschema
- Writes output as JSON or YAML (--format json|yaml). If PyYAML is not installed, falls back to JSON.
Usage:
  python configgen.py --schema schema.json --out config.yaml --format yaml
"""

import argparse
import json
import sys

try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False

try:
    import jsonschema
except Exception:
    print("Missing dependency: install jsonschema (pip install jsonschema).", file=sys.stderr)
    sys.exit(1)


def prompt_basic(name, prop_schema):
    typ = prop_schema.get("type", "string")
    title = prop_schema.get("title", name)
    desc = prop_schema.get("description", "")
    default = prop_schema.get("default")
    enum = prop_schema.get("enum")

    label = f"{title}"
    if desc:
        label += f" — {desc}"
    if enum:
        label += f" (options: {', '.join(map(str, enum))})"
    if default is not None:
        label += f" [default: {default}]"
    label += ": "

    while True:
        raw = input(label).strip()
        if raw == "" and default is not None:
            value = default
            break
        if raw == "":
            # empty and no default => None (if not required will be omitted later)
            value = None
            break

        try:
            if enum:
                if raw not in list(map(str, enum)):
                    print("  >> must be one of:", ", ".join(map(str, enum)))
                    continue
                # choose exact typed enum value
                # find matching element in enum with same string repr
                matched = next((e for e in enum if str(e) == raw), raw)
                value = matched
            elif typ == "string":
                value = raw
            elif typ == "integer":
                value = int(raw)
            elif typ == "number":
                value = float(raw)
            elif typ == "boolean":
                if raw.lower() in ("1", "true", "t", "y", "yes"):
                    value = True
                elif raw.lower() in ("0", "false", "f", "n", "no"):
                    value = False
                else:
                    print("  >> enter true/false (or yes/no, 1/0)")
                    continue
            else:
                # unknown type: keep as string
                value = raw
            break
        except ValueError:
            print(f"  >> could not convert input to {typ}, try again.")
    return value


def build_config_from_schema(schema):
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    cfg = {}

    print("Enter values for configuration fields (press Enter to use default or leave blank if optional).")
    for name, prop_schema in props.items():
        value = prompt_basic(name, prop_schema)
        if value is None and name not in required and "default" not in prop_schema:
            # omit optional unset field
            continue
        cfg[name] = value
    return cfg


def main():
    p = argparse.ArgumentParser(description="Config generator from JSON Schema")
    p.add_argument("--schema", "-s", required=True, help="Path to JSON Schema file")
    p.add_argument("--out", "-o", required=True, help="Output filename (extension decides format if --format not set)")
    p.add_argument("--format", "-f", choices=["json", "yaml"], help="Output format (json or yaml). If omitted, inferred from out extension.")
    args = p.parse_args()

    with open(args.schema, "r", encoding="utf-8") as fh:
        schema = json.load(fh)

    cfg = build_config_from_schema(schema)

    # validate
    try:
        jsonschema.validate(instance=cfg, schema=schema)
    except jsonschema.ValidationError as e:
        print("Validation error:", e.message, file=sys.stderr)
        print("Full error:", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(2)

    out_format = args.format
    if not out_format:
        if args.out.lower().endswith((".yaml", ".yml")):
            out_format = "yaml"
        else:
            out_format = "json"

    if out_format == "yaml" and not HAS_YAML:
        print("PyYAML not installed; falling back to JSON output.", file=sys.stderr)
        out_format = "json"

    if out_format == "json":
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            yaml.safe_dump(cfg, fh, allow_unicode=True)

    print(f"Wrote config to {args.out} ({out_format}).")


if __name__ == "__main__":
    main()
