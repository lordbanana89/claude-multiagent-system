#!/usr/bin/env python3
"""
Figma API Helper Script
Usa questo script per estrarre design da Figma
"""

import requests
import json
import sys

FIGMA_TOKEN = "YOUR_FIGMA_TOKEN_HERE"

def get_figma_file(file_url):
    """Estrae informazioni da un file Figma"""

    # Estrai file ID dall'URL
    # URL format: https://www.figma.com/file/FILE_ID/NAME
    if "figma.com/file/" in file_url:
        file_id = file_url.split("/file/")[1].split("/")[0]
    else:
        file_id = file_url

    headers = {
        "X-Figma-Token": FIGMA_TOKEN
    }

    # Get file info
    response = requests.get(
        f"https://api.figma.com/v1/files/{file_id}",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()

        # Estrai informazioni utili
        result = {
            "name": data.get("name", "Unknown"),
            "lastModified": data.get("lastModified", "Unknown"),
            "components": len(data.get("components", {})),
            "styles": len(data.get("styles", {})),
            "document": extract_structure(data.get("document", {}))
        }

        return result
    else:
        return {"error": f"Failed to fetch: {response.status_code}"}

def extract_structure(node, depth=0, max_depth=3):
    """Estrae la struttura del documento"""
    if depth > max_depth:
        return None

    structure = {
        "type": node.get("type", "Unknown"),
        "name": node.get("name", "Unknown")
    }

    if "children" in node and depth < max_depth:
        structure["children"] = [
            extract_structure(child, depth + 1, max_depth)
            for child in node.get("children", [])[:5]  # Max 5 children per level
        ]

    return structure

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 figma_api.py <FIGMA_URL_OR_FILE_ID>")
        sys.exit(1)

    file_url = sys.argv[1]
    result = get_figma_file(file_url)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()