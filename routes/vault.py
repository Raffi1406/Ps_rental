"""
routes/vault.py
Modul INTI manajemen S3 aplikasi ini ("Cloud Vault"): browsing folder/file,
upload, download, delete, rename, create folder, dan preview gambar.
Bisa dipakai untuk menjelajah seluruh bucket vault (semua transaksi) maupun
dibuka langsung dari halaman detail satu transaksi (prefix sudah terisi).
"""

from flask import (
    Blueprint, render_template, current_app, flash,
    redirect, url_for, request, jsonify
)
from services.s3_service import S3ServiceError
from utils.helper import format_bytes, is_image_file, build_breadcrumbs, parent_prefix, secure_filename_simple

vault_bp = Blueprint("vault", __name__)


@vault_bp.route("/vault")
def browse():
    s3 = current_app.s3_service
    root_prefix = current_app.config["VAULT_ROOT_PREFIX"]
    prefix = request.args.get("prefix", root_prefix)

    try:
        folders, files = s3.list_objects(prefix)
    except S3ServiceError as e:
        flash(str(e), "danger")
        return redirect(url_for("dashboard.index"))

    image_exts = current_app.config["IMAGE_EXTENSIONS"]
    for f in files:
        f["size_human"] = format_bytes(f["size"])
        f["is_image"] = is_image_file(f["name"], image_exts)

    breadcrumbs = build_breadcrumbs(prefix, root_prefix)
    parent = parent_prefix(prefix, root_prefix)

    return render_template(
        "vault.html",
        prefix=prefix,
        root_prefix=root_prefix,
        folders=folders,
        files=files,
        breadcrumbs=breadcrumbs,
        parent_prefix=parent,
        bucket=s3.bucket,
    )


@vault_bp.route("/vault/folder/create", methods=["POST"])
def create_folder():
    s3 = current_app.s3_service
    prefix = request.form.get("prefix", "")
    folder_name = request.form.get("folder_name", "").strip()

    if not folder_name:
        flash("Nama folder tidak boleh kosong.", "warning")
    else:
        try:
            s3.create_folder(prefix, folder_name)
            flash(f"Folder '{folder_name}' berhasil dibuat.", "success")
        except S3ServiceError as e:
            flash(str(e), "danger")

    return redirect(url_for("vault.browse", prefix=prefix))


@vault_bp.route("/vault/upload", methods=["POST"])
def upload():
    s3 = current_app.s3_service
    prefix = request.form.get("prefix", "")
    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        flash("Pilih minimal satu file untuk diunggah.", "warning")
        return redirect(url_for("vault.browse", prefix=prefix))

    uploaded, failed = [], []
    for f in files:
        filename = secure_filename_simple(f.filename)
        try:
            s3.upload_file(prefix, f, filename)
            uploaded.append(filename)
        except S3ServiceError as e:
            failed.append((filename, str(e)))

    if uploaded:
        flash(f"{len(uploaded)} file berhasil diunggah: {', '.join(uploaded)}", "success")
    for filename, error in failed:
        flash(f"Gagal mengunggah '{filename}': {error}", "danger")

    return redirect(url_for("vault.browse", prefix=prefix))


@vault_bp.route("/vault/delete", methods=["POST"])
def delete():
    s3 = current_app.s3_service
    key = request.form.get("key")
    is_folder = request.form.get("is_folder") == "1"
    prefix = request.form.get("prefix", "")

    try:
        if is_folder:
            s3.delete_folder(key)
            flash("Folder berhasil dihapus.", "success")
        else:
            s3.delete_object(key)
            flash("File berhasil dihapus.", "success")
    except S3ServiceError as e:
        flash(str(e), "danger")

    return redirect(url_for("vault.browse", prefix=prefix))


@vault_bp.route("/vault/rename", methods=["POST"])
def rename():
    s3 = current_app.s3_service
    old_key = request.form.get("old_key")
    new_name = request.form.get("new_name", "").strip()
    is_folder = request.form.get("is_folder") == "1"
    prefix = request.form.get("prefix", "")

    if not new_name:
        flash("Nama baru tidak boleh kosong.", "warning")
        return redirect(url_for("vault.browse", prefix=prefix))

    try:
        if is_folder:
            old_prefix = old_key if old_key.endswith("/") else old_key + "/"
            new_prefix = f"{prefix}{new_name}/"
            s3.rename_folder(old_prefix, new_prefix)
            flash("Folder berhasil di-rename.", "success")
        else:
            parent = old_key.rsplit("/", 1)[0] + "/" if "/" in old_key else ""
            new_key = f"{parent}{new_name}"
            s3.rename_object(old_key, new_key)
            flash("File berhasil di-rename.", "success")
    except S3ServiceError as e:
        flash(str(e), "danger")

    return redirect(url_for("vault.browse", prefix=prefix))


@vault_bp.route("/vault/download")
def download():
    s3 = current_app.s3_service
    key = request.args.get("key")
    try:
        url = s3.generate_presigned_url(key)
        return redirect(url)
    except S3ServiceError as e:
        flash(str(e), "danger")
        return redirect(url_for("vault.browse"))


@vault_bp.route("/vault/preview")
def preview():
    s3 = current_app.s3_service
    key = request.args.get("key")
    try:
        url = s3.generate_presigned_url(key, expires_in=600)
        return jsonify({"success": True, "url": url})
    except S3ServiceError as e:
        return jsonify({"success": False, "message": str(e)}), 400
