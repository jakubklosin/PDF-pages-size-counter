const selectButton = document.querySelector("#select-files");
const fileInput = document.querySelector("#pdf-files");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const sizePanel = document.querySelector("#size-panel");
const sizeTable = document.querySelector("#size-table");
const filesPanel = document.querySelector("#files-panel");
const filesContainer = document.querySelector("#files");
const languageButtons = document.querySelectorAll("[data-language]");

const translations = {
  en: {
    eyebrow: "Desktop PDF Analyzer",
    title: "Count page sizes, print area, and color usage.",
    description:
      "Select one or more PDF files to calculate A-series page counts, custom dimensions, square meters of paper, and black-and-white versus color pages.",
    selectFiles: "Select PDF files",
    analyzeFiles: "Analyze PDF files",
    pagesBySize: "Pages by size",
    filesTitle: "Files",
    chooseFiles: "Choose one or more PDF files.",
    noFiles: "No files selected.",
    analyzing: "Analyzing {count} file{plural}...",
    complete: "Analysis complete.",
    failed: "Analysis failed: {error}",
    files: "Files",
    pages: "Pages",
    paperArea: "Paper area",
    measuredArea: "Measured area",
    bwPages: "B&W pages",
    colorPages: "Color pages",
    bwPaperArea: "B&W paper area",
    colorPaperArea: "Color paper area",
    a4BwPages: "A4 B&W",
    a4ColorPages: "A4 color",
    a3BwPages: "A3 B&W",
    a3ColorPages: "A3 color",
    failedFiles: "Failed files",
    pageSize: "Page size",
    area: "Area",
    unableToAnalyze: "Unable to analyze file.",
    customPages: "Custom pages",
    page: "Page",
    classification: "Classification",
    dimensions: "Dimensions",
    billableSize: "Billable size",
    billableArea: "Billable area",
    color: "Color",
    bw: "B&W",
    fileMeta:
      "{pages} pages · {paperArea} m² paper · {measuredArea} m² measured · {bwArea} m² B&W · {colorArea} m² color · {bw} B&W · {color} color",
  },
  pl: {
    eyebrow: "Desktopowy analizator PDF",
    title: "Policz formaty stron, powierzchnię papieru i kolor.",
    description:
      "Wybierz jeden lub kilka plików PDF, aby policzyć formaty A, niestandardowe wymiary, metry kwadratowe papieru oraz strony czarno-białe i kolorowe.",
    selectFiles: "Wybierz pliki PDF",
    analyzeFiles: "Analizuj pliki PDF",
    pagesBySize: "Strony według formatu",
    filesTitle: "Pliki",
    chooseFiles: "Wybierz jeden lub kilka plików PDF.",
    noFiles: "Nie wybrano plików.",
    analyzing: "Analizuję {count} plik{plural}...",
    complete: "Analiza zakończona.",
    failed: "Analiza nie powiodła się: {error}",
    files: "Pliki",
    pages: "Strony",
    paperArea: "Powierzchnia papieru",
    measuredArea: "Powierzchnia zmierzona",
    bwPages: "Strony cz.-b.",
    colorPages: "Strony kolorowe",
    bwPaperArea: "Pow. papieru cz.-b.",
    colorPaperArea: "Pow. papieru kolor",
    a4BwPages: "A4 cz.-b.",
    a4ColorPages: "A4 kolor",
    a3BwPages: "A3 cz.-b.",
    a3ColorPages: "A3 kolor",
    failedFiles: "Błędne pliki",
    pageSize: "Format strony",
    area: "Powierzchnia",
    unableToAnalyze: "Nie można przeanalizować pliku.",
    customPages: "Strony niestandardowe",
    page: "Strona",
    classification: "Klasyfikacja",
    dimensions: "Wymiary",
    billableSize: "Format rozliczeniowy",
    billableArea: "Pow. rozliczeniowa",
    color: "Kolor",
    bw: "Cz.-b.",
    fileMeta:
      "{pages} stron · {paperArea} m² papieru · {measuredArea} m² zmierzone · {bwArea} m² cz.-b. · {colorArea} m² kolor · {bw} cz.-b. · {color} kolor",
  },
};

let currentLanguage = localStorage.getItem("pdfAnalyzerLanguage") || "en";
let latestResult = null;
const isWebMode = window.location.protocol.startsWith("http");

document.body.classList.toggle("web-mode", isWebMode);

applyLanguage();

selectButton.addEventListener("click", async () => {
  setStatus(t("chooseFiles"), "info");
  selectButton.disabled = true;

  try {
    const result = isWebMode ? await analyzeUploadedFiles() : await analyzeDesktopFiles();
    if (!result) {
      return;
    }
    latestResult = result;
    renderResults(result);
    setStatus(t("complete"), "info");
  } catch (error) {
    console.error(error);
    setStatus(t("failed", { error: error.message || error }), "error");
  } finally {
    selectButton.disabled = false;
  }
});

languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentLanguage = button.dataset.language || "en";
    localStorage.setItem("pdfAnalyzerLanguage", currentLanguage);
    applyLanguage();
    if (latestResult) {
      renderResults(latestResult);
    }
  });
});

function renderResults(result) {
  renderSummary(result.summary);
  renderSizeTable(result.summary);
  renderFiles(result.files);
}

async function analyzeDesktopFiles() {
  const paths = await window.pywebview.api.select_pdf_files();
  if (!paths.length) {
    setStatus(t("noFiles"), "info");
    return null;
  }

  setStatus(
    t("analyzing", {
      count: paths.length,
      plural: paths.length === 1 ? "" : "s",
    }),
    "info",
  );
  return window.pywebview.api.analyze_files(paths);
}

async function analyzeUploadedFiles() {
  const files = Array.from(fileInput.files || []);
  if (!files.length) {
    setStatus(t("noFiles"), "info");
    return null;
  }

  setStatus(
    t("analyzing", {
      count: files.length,
      plural: files.length === 1 ? "" : "s",
    }),
    "info",
  );

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
  return result;
}

function renderSummary(data) {
  summary.classList.remove("hidden");
  summary.innerHTML = [
    summaryCard(t("files"), `${data.successful_files}/${data.total_files}`),
    summaryCard(t("pages"), data.total_pages),
    summaryCard(t("paperArea"), `${formatNumber(data.total_area_m2)} m²`),
    summaryCard(t("measuredArea"), `${formatNumber(data.measured_area_m2)} m²`),
    summaryCard(t("bwPaperArea"), `${formatNumber(data.color_area_m2.black_white)} m²`),
    summaryCard(t("colorPaperArea"), `${formatNumber(data.color_area_m2.color)} m²`),
    summaryCard(t("bwPages"), data.color_counts.black_white),
    summaryCard(t("colorPages"), data.color_counts.color),
    summaryCard(t("a4BwPages"), data.regular_page_color_counts.A4.black_white),
    summaryCard(t("a4ColorPages"), data.regular_page_color_counts.A4.color),
    summaryCard(t("a3BwPages"), data.regular_page_color_counts.A3.black_white),
    summaryCard(t("a3ColorPages"), data.regular_page_color_counts.A3.color),
    summaryCard(t("failedFiles"), data.failed_files),
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
    [t("pageSize"), t("pages"), t("paperArea")],
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
        <p class="file-meta">${escapeHtml(file.error || t("unableToAnalyze"))}</p>
      </article>
    `;
  }

  const customPages = file.pages
    .filter((page) => page.size_category !== "standard")
    .map((page) => [
      page.page_number,
      page.size_name,
      page.size_note || `${formatNumber(page.width_mm)} mm x ${formatNumber(page.height_mm)} mm`,
      page.billable_size_name,
      `${formatNumber(page.billable_area_m2)} m²`,
      page.color_mode === "color" ? t("color") : t("bw"),
    ]);

  return `
    <article class="file-card">
      <h3>${escapeHtml(file.file_name)}</h3>
      <p class="file-meta">
        ${escapeHtml(
          t("fileMeta", {
            pages: file.total_pages,
            paperArea: formatNumber(file.total_area_m2),
            measuredArea: formatNumber(file.measured_area_m2),
            bwArea: formatNumber(file.color_area_m2.black_white),
            colorArea: formatNumber(file.color_area_m2.color),
            bw: file.color_counts.black_white,
            color: file.color_counts.color,
          }),
        )}
      </p>
      ${makeTable(
        [t("pageSize"), t("pages"), t("paperArea")],
        Object.entries(file.page_size_counts).map(([name, count]) => [
          name,
          count,
          `${formatNumber(file.page_size_area_m2[name] ?? 0)} m²`,
        ]),
      )}
      ${
        customPages.length
          ? `<h4>${escapeHtml(t("customPages"))}</h4>${makeTable(
              [
                t("page"),
                t("classification"),
                t("dimensions"),
                t("billableSize"),
                t("billableArea"),
                t("color"),
              ],
              customPages,
            )}`
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
  return Number(value).toLocaleString(currentLanguage === "pl" ? "pl-PL" : undefined, {
    maximumFractionDigits: 4,
    minimumFractionDigits: 0,
  });
}

function applyLanguage() {
  document.documentElement.lang = currentLanguage;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  selectButton.textContent = t(isWebMode ? "analyzeFiles" : "selectFiles");
  languageButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.language === currentLanguage);
  });
}

function t(key, values = {}) {
  let text = translations[currentLanguage][key] || translations.en[key] || key;
  Object.entries(values).forEach(([name, value]) => {
    text = text.replace(`{${name}}`, String(value));
  });
  return text;
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
