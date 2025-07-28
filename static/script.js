const fileInput = document.getElementById("file-upload");
const fileNameDisplay = document.getElementById("file-name");
const companyTextarea = document.getElementById("company_names");
const companyCountDisplay = document.getElementById("company-count");
const submitButton = document.getElementById("submit-button");
const form = document.getElementById("upload-form");
const loading = document.getElementById("loading");
const toastContainer = document.getElementById("toast-container");
const progressList = document.getElementById("progress-list");
const downloadSection = document.getElementById("download-section");
const dropArea = document.getElementById("drop-area");

let resultFileUrl = "";
let logFileUrl = "";

// Drag Over
dropArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  const isValid = [...e.dataTransfer.items].some(item =>
    item.kind === "file" && item.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  );
  dropArea.classList.add(isValid ? "dragover-valid" : "dragover-invalid");
});

// Drag Leave
dropArea.addEventListener("dragleave", () => {
  dropArea.classList.remove("dragover-valid", "dragover-invalid");
});

// Drop
dropArea.addEventListener("drop", (e) => {
  e.preventDefault();
  dropArea.classList.remove("dragover-valid", "dragover-invalid");

  const file = e.dataTransfer.files[0];
  if (!file || !file.name.endsWith(".xlsx")) {
    showToast("❌ Only .xlsx files are supported.", "error");
    return;
  }

  fileInput.files = e.dataTransfer.files;
  const event = new Event("change");
  fileInput.dispatchEvent(event);
});

// Show selected file name
fileInput.addEventListener("change", () => {
  const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : "No file selected";
  fileNameDisplay.textContent = fileName;
  validateForm();
});

// Count textarea lines and reset file input if text used
companyTextarea.addEventListener("input", () => {
  fileInput.value = null;
  fileNameDisplay.textContent = "No file selected";

  const lines = companyTextarea.value.split("\n").filter(line => line.trim() !== "");
  companyCountDisplay.textContent = `${lines.length} compan${lines.length === 1 ? 'y' : 'ies'} entered`;
  validateForm();
});

// Disable submit if both inputs are empty
function validateForm() {
  const hasFile = fileInput.files.length > 0;
  const hasText = companyTextarea.value.trim().length > 0;
  submitButton.disabled = !(hasFile || hasText);
}

// Handle AJAX form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  loading.classList.add("visible");
  await new Promise(resolve => setTimeout(resolve, 200)); // slight delay for smooth spinner show

  progressList.innerHTML = "";
  downloadSection.style.display = "none";
  showToast("Submitting form...", "info");

  const formData = new FormData(form);

  try {
    const response = await fetch("/process", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (result.error) {
      showToast(result.error, "error");
      loading.classList.remove("visible");
      return;
    }

    resultFileUrl = result.file_url;
    logFileUrl = result.log_url;

    for (const entry of result.statuses) {
      const li = document.createElement("li");
      li.textContent = `✔ ${entry.company} — ${entry.status}`;
      li.style.opacity = 0;
      li.style.transition = "opacity 0.3s ease";
      progressList.appendChild(li);
      await new Promise(resolve => setTimeout(resolve, 120)); // show each item with delay
      li.style.opacity = 1;
    }

    showToast("✅ Processing complete! Files ready to download.");
    downloadSection.style.display = "block";

    // Auto-download confirmation
    if (confirm("Do you want to download the files now?")) {
      const resultLink = document.createElement("a");
      resultLink.href = resultFileUrl;
      resultLink.download = "";
      resultLink.click();

      const logLink = document.createElement("a");
      logLink.href = logFileUrl;
      logLink.download = "";
      logLink.click();
    }

  } catch (error) {
    console.error(error);
    showToast("❌ Error during processing.", "error");
  } finally {
    loading.classList.remove("visible");
  }
});

// Toast notification system
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.classList.add("toast");
  if (type === "error") toast.classList.add("error");
  if (type === "info") toast.style.backgroundColor = "#3498db";
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}