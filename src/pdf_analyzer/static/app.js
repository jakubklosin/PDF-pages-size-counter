const selectButton = document.querySelector("#select-files");
const fileInput = document.querySelector("#pdf-files");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const sizePanel = document.querySelector("#size-panel");
const sizeTable = document.querySelector("#size-table");
const filesPanel = document.querySelector("#files-panel");
const filesContainer = document.querySelector("#files");

selectButton.addEventListener("click", async () => {
  const files = Array.from(fileInput.files || []);
  if (!files.length) {
    setStatus("Choose one or more PDF files first.", "info");
    return;
  }

  selectButton.disabled = true;

  try {
    setStatus(`Analyzing ${files.length} file${files.length === 1 ? "" : "s"}...`, "info");
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || "Analysis failed.");
    }

    renderResults(result);
    setStatus("Analysis complete.", "info");
  } catch (error) {
    console.error(error);
    setStatus(`Analysis failed: ${error}`, "error");
  } finally {
    selectButton.disabled = false;
  }
});

function renderResults(result) {
  renderSummary(result.summary);
  renderSizeTable(result.summary);
  renderFiles(result.files);
}

function renderSummary(data) {
  summary.classList.remove("hidden");
  summary.innerHTML = [
    summaryCard("Files", `${data.successful_files}/${data.total_files}`),
    summaryCard("Pages", data.total_pages),
    summaryCard("Paper area", `${formatNumber(data.total_area_m2)} m²`),
    summaryCard("Area without A4", `${formatNumber(data.total_area_excluding_a4_m2)} m²`),
    summaryCard("B&W pages", data.color_counts.black_white),
    summaryCard("Color pages", data.color_counts.color),
    summaryCard("Failed files", data.failed_files),
  ].join("");
}

function summaryCard(label, value) {
  return `
    <article class="card">
      <span>${escapeHtml(label)}</span>
      <strong class="card-value">${escapeHtml(String(value))}</strong>
    </article>
  `;
}

function renderSizeTable(data) {
  sizePanel.classList.remove("hidden");
  sizeTable.innerHTML = makeTable(
    ["Page size", "Pages", "Area"],
    Object.entries(data.page_size_counts).map(([name, count]) => [
      name,
      count,
      `${formatNumber(data.page_size_area_m2[name] ?? 0)} m²`,
    ]),
  );
}

function renderFiles(files) {
  filesPanel.classList.remove("hidden");
  filesContainer.classList.add("files");
  filesContainer.innerHTML = files.map(renderFile).join("");
}

function renderFile(file) {
  if (!file.success) {
    return `
      <article class="file-card error">
        <h3>${escapeHtml(file.file_name)}</h3>
        <p class="file-meta">${escapeHtml(file.error || "Unable to analyze file.")}</p>
      </article>
    `;
  }

  const customPages = file.pages
    .filter((page) => page.size_category !== "standard")
    .map((page) => [
      page.page_number,
      page.size_name,
      page.size_note || `${formatNumber(page.width_mm)} mm x ${formatNumber(page.height_mm)} mm`,
      page.color_mode === "color" ? "Color" : "B&W",
    ]);

  return `
    <article class="file-card">
      <h3>${escapeHtml(file.file_name)}</h3>
      <p class="file-meta">
        ${file.total_pages} pages · ${formatNumber(file.total_area_m2)} m² ·
        ${formatNumber(file.total_area_excluding_a4_m2)} m² without A4 ·
        ${file.color_counts.black_white} B&W · ${file.color_counts.color} color
      </p>
      ${makeTable(
        ["Page size", "Pages", "Area"],
        Object.entries(file.page_size_counts).map(([name, count]) => [
          name,
          count,
          `${formatNumber(file.page_size_area_m2[name] ?? 0)} m²`,
        ]),
      )}
      ${
        customPages.length
          ? `<h4>Custom pages</h4>${makeTable(["Page", "Classification", "Dimensions", "Color"], customPages)}`
          : ""
      }
    </article>
  `;
}

function makeTable(headers, rows) {
  if (!rows.length) {
    return "<p>No data.</p>";
  }

  return `
    <table>
      <thead>
        <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) =>
              `<tr>${row.map((cell) => `<td>${escapeHtml(String(cell))}</td>`).join("")}</tr>`,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function setStatus(message, type) {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

function formatNumber(value) {
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 4,
    minimumFractionDigits: 0,
  });
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => {
    const replacements = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return replacements[character];
  });
}
