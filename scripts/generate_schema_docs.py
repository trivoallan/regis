import json
import os
import re

import jsonschema2md

SCHEMA_DIR = "regis_cli/schemas"
DOCS_DIR = "docs/modules/ROOT/pages/schemas"


def convert_md_to_adoc(md_lines):
    adoc_lines = []
    for line in md_lines:
        line = line.rstrip()  # remove trailing whitespaces/newlines from library

        # Convert Headers: # -> =, ## -> ==, ### -> ===
        header_match = re.match(r"^(#+)\s+(.*)", line)
        if header_match:
            hashes = len(header_match.group(1))
            text = header_match.group(2)
            adoc_lines.append(f"{'=' * hashes} {text}")
            continue

        # Convert Links: [Text](#link/id) -> <<link_id,Text>>
        def replace_link(match):
            text = match.group(1)
            link_id = match.group(2).replace("/", "_")
            return f"<<{link_id},{text}>>"

        line = re.sub(r"\[([^\]]+)\]\(#([^\)]+)\)", replace_link, line)

        # Convert HTML Anchors: <a id="property/id"></a> -> [[property_id]]
        def replace_anchor(match):
            anchor_id = match.group(1).replace("/", "_")
            return f"[[{anchor_id}]]"

        line = re.sub(r'<a id="([^"]+)"></a>', replace_anchor, line)

        # Convert nested bullet points: '  - ' -> '** '
        bullet_match = re.match(r"^(\s*)-\s+(.*)", line)
        if bullet_match:
            spaces = len(bullet_match.group(1).replace("\t", "    "))
            level = (spaces // 2) + 1
            line = f"{'*' * level} {bullet_match.group(2)}"

        # Basic bold / code conversion usually works as-is in asciidoc if not too complex,
        # but jsonschema2md outputs standard Markdown code blocks ` ` ` which we need to convert to ----
        if line.startswith("```"):
            adoc_lines.append("----")
            continue

        adoc_lines.append(line)

    return "\n".join(adoc_lines)


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    parser = jsonschema2md.Parser(examples_as_yaml=False, show_examples="all")

    for filename in os.listdir(SCHEMA_DIR):
        if not filename.endswith(".schema.json"):
            continue

        filepath = os.path.join(SCHEMA_DIR, filename)
        with open(filepath, "r") as f:
            schema = json.load(f)

        # Generate markdown using jsonschema2md
        md_lines = parser.parse_schema(schema)

        # Convert to basic AsciiDoc
        adoc_content = convert_md_to_adoc(md_lines)

        basename = filename.replace(".schema.json", "")
        out_filepath = os.path.join(DOCS_DIR, f"{basename}.adoc")

        with open(out_filepath, "w") as f:
            f.write(adoc_content)

        print(f"Generated {out_filepath}")


if __name__ == "__main__":
    main()
