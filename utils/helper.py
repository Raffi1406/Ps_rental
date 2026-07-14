"""
utils/helper.py
Kumpulan fungsi bantuan yang dipakai lintas routes & templates.
"""

import os


def format_bytes(size):
    if size is None:
        return "-"
    size = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_rupiah(amount):
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "Rp 0"
    return "Rp " + f"{amount:,}".replace(",", ".")


def is_image_file(filename, image_extensions):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in image_extensions


def build_breadcrumbs(prefix, root_prefix=""):
    """Breadcrumb relatif terhadap root_prefix (mis. 'rentals/')."""
    if not prefix:
        return []
    display = prefix[len(root_prefix):] if prefix.startswith(root_prefix) else prefix
    parts = [p for p in display.split("/") if p]
    breadcrumbs = []
    accumulated = root_prefix
    for part in parts:
        accumulated += part + "/"
        breadcrumbs.append({"name": part, "path": accumulated})
    return breadcrumbs


def secure_filename_simple(filename):
    filename = os.path.basename(filename)
    keep_chars = (" ", ".", "_", "-", "(", ")")
    cleaned = "".join(c for c in filename if c.isalnum() or c in keep_chars).strip()
    return cleaned or "file"


def parent_prefix(prefix, root_prefix=""):
    if not prefix or prefix == root_prefix:
        return None
    parts = [p for p in prefix[len(root_prefix):].split("/") if p]
    if len(parts) <= 1:
        return root_prefix
    return root_prefix + "/".join(parts[:-1]) + "/"
