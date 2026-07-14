/* ==========================================================================
   PS Rental Cloud Vault — app.js
   Modal handling, drag-and-drop upload, rename/delete prompt, dan preview
   gambar lewat presigned URL (AJAX ke /vault/preview).
   ========================================================================== */

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

document.addEventListener("click", (e) => {
  document.querySelectorAll(".modal-overlay.open").forEach((overlay) => {
    if (e.target === overlay) overlay.classList.remove("open");
  });
});

function promptRename(key, currentName, isFolder) {
  document.getElementById("renameOldKey").value = key;
  document.getElementById("renameIsFolder").value = isFolder ? "1" : "0";
  document.getElementById("renameNewName").value = currentName;
  openModal("renameModal");
}

function promptDelete(key, isFolder) {
  document.getElementById("deleteKey").value = key;
  document.getElementById("deleteIsFolder").value = isFolder ? "1" : "0";
  openModal("deleteModal");
}

function previewImage(key) {
  const url = `/vault/preview?key=${encodeURIComponent(key)}`;
  fetch(url)
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("previewImg").src = data.url;
        openModal("previewModal");
      } else {
        alert("Gagal memuat preview: " + data.message);
      }
    })
    .catch((err) => alert("Terjadi kesalahan: " + err));
}

/* ---------------- Drag & Drop Upload ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  const dropzones = document.querySelectorAll(".dropzone");

  dropzones.forEach((zone) => {
    const input = zone.querySelector('input[type="file"]');
    const listBox = zone.parentElement.querySelector(".file-preview-list");

    ["dragenter", "dragover"].forEach((evt) => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
      });
    });

    zone.addEventListener("drop", (e) => {
      if (input && e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        updateFileList(input, listBox);
      }
    });

    if (input) {
      input.addEventListener("change", () => updateFileList(input, listBox));
    }
  });

  function updateFileList(input, listBox) {
    if (!listBox) return;
    const names = Array.from(input.files).map((f) => f.name);
    listBox.textContent = names.length ? `Dipilih: ${names.join(", ")}` : "";
  }
});
