document.addEventListener("DOMContentLoaded", () => {

  const processForm = document.getElementById("processForm");
  const videoUrlInput = document.getElementById("videoUrl");
  const videoLangInput = document.getElementById("videoLang");
  const processBtn = document.getElementById("processBtn");
  const btnText = processBtn.querySelector(".btn-text");
  const spinnerLoader = processBtn.querySelector(".spinner-loader");

  const processingBanner = document.getElementById("processingBanner");
  const statusTitle = document.getElementById("statusTitle");
  const statusDetail = document.getElementById("statusDetail");

  const activeVideoCard = document.getElementById("activeVideoCard");
  const activeVideoTitle = document.getElementById("activeVideoTitle");
  const activeVideoIdPill = document.getElementById("activeVideoIdPill");

  const notesPlaceholder = document.getElementById("notesPlaceholder");
  const notesBody = document.getElementById("notesBody");
  const topicsContent = document.getElementById("topicsContent");
  const notesContent = document.getElementById("notesContent");
  const downloadPdfBtn = document.getElementById("downloadPdfBtn");

  const resetBtn = document.getElementById("resetBtn");

  let currentVideoData = {
    title: "",
    url: "",
    videoId: "",
    topics: "",
    notes: ""
  };

  function renderMarkdownToHtml(markdown) {
    if (!markdown) return "";
    let html = markdown;

    html = html
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    html = html.replace(/\*\*\*(.*?)\*\*\*/gim, "<strong><em>$1</em></strong>");
    html = html.replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>");
    html = html.replace(/\*(.*?)\*/gim, "<em>$1</em>");

    html = html.replace(/`([^`]+)`/gim, "<code>$1</code>");

    const lines = html.split("\n");
    let inUl = false;
    let inOl = false;
    let processedLines = [];

    for (let line of lines) {
      const trimmed = line.trim();
      if (/^[-*•]\s+(.*)/.test(trimmed)) {
        if (inOl) {
          processedLines.push("</ol>");
          inOl = false;
        }
        if (!inUl) {
          processedLines.push("<ul>");
          inUl = true;
        }
        processedLines.push(`<li>${trimmed.replace(/^[-*•]\s+/, "")}</li>`);
      } else if (/^\d+[\.\\)]\s+(.*)/.test(trimmed)) {
        if (inUl) {
          processedLines.push("</ul>");
          inUl = false;
        }
        if (!inOl) {
          processedLines.push("<ol>");
          inOl = true;
        }
        processedLines.push(`<li>${trimmed.replace(/^\d+[\.\\)]\s+/, "")}</li>`);
      } else {
        if (inUl) {
          processedLines.push("</ul>");
          inUl = false;
        }
        if (inOl) {
          processedLines.push("</ol>");
          inOl = false;
        }
        if (trimmed.length > 0 && !trimmed.startsWith("<h")) {
          processedLines.push(`<p>${trimmed}</p>`);
        } else if (trimmed.length > 0) {
          processedLines.push(trimmed);
        }
      }
    }

    if (inUl) processedLines.push("</ul>");
    if (inOl) processedLines.push("</ol>");

    return processedLines.join("\n");
  }

  processForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = videoUrlInput.value.trim();
    const language = videoLangInput.value.trim() || "en";

    if (!url) return;

    processBtn.disabled = true;
    btnText.classList.add("hidden");
    spinnerLoader.classList.remove("hidden");

    processingBanner.classList.remove("hidden");
    statusTitle.textContent = "Processing Video Content...";
    statusDetail.textContent = "Step 1 of 3: Fetching transcript & translating if necessary...";

    const stageTimer1 = setTimeout(() => {
      statusDetail.textContent = "Step 2 of 3: Synthesizing notes & extracting key topics...";
    }, 4000);

    const stageTimer2 = setTimeout(() => {
      statusDetail.textContent = "Step 3 of 3: Indexing semantic vectors into ChromaDB...";
    }, 9000);

    try {
      const response = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, language })
      });

      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);

      const result = await response.json();

      if (!response.ok || result.status !== "success") {
        throw new Error(result.message || "Failed to process video");
      }

      const data = result.data;
      currentVideoData = {
        title: data.title,
        url: data.url,
        videoId: data.videoId,
        topics: data.topics,
        notes: data.notes
      };

      activeVideoTitle.textContent = data.title;
      activeVideoIdPill.textContent = `ID: ${data.videoId}`;
      activeVideoCard.classList.remove("hidden");

      topicsContent.innerHTML = renderMarkdownToHtml(data.topics);
      notesContent.innerHTML = renderMarkdownToHtml(data.notes);

      notesPlaceholder.classList.add("hidden");
      notesBody.classList.remove("hidden");

      downloadPdfBtn.disabled = false;

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      processBtn.disabled = false;
      btnText.classList.remove("hidden");
      spinnerLoader.classList.add("hidden");
      processingBanner.classList.add("hidden");
    }
  });

  downloadPdfBtn.addEventListener("click", async () => {
    if (!currentVideoData.notes && !currentVideoData.topics) {
      alert("Please process a video first.");
      return;
    }

    downloadPdfBtn.disabled = true;
    const originalText = downloadPdfBtn.innerHTML;
    downloadPdfBtn.innerHTML = `<span>Generating PDF...</span>`;

    try {
      const response = await fetch("/api/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: currentVideoData.title,
          url: currentVideoData.url,
          notes: currentVideoData.notes,
          topics: currentVideoData.topics
        })
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.message || "Could not generate PDF");
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const downloadLink = document.createElement("a");
      downloadLink.href = blobUrl;

      const disposition = response.headers.get("Content-Disposition");
      let filename = "ClipSutra_Notes.pdf";
      if (disposition && disposition.indexOf("filename=") !== -1) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, "");
        }
      }

      downloadLink.download = filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      window.URL.revokeObjectURL(blobUrl);

    } catch (err) {
      alert("Error downloading PDF: " + err.message);
    } finally {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.innerHTML = originalText;
    }
  });

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  resetBtn.addEventListener("click", async () => {
    if (confirm("Reset current video session?")) {
      await fetch("/api/reset", { method: "POST" });
      window.location.reload();
    }
  });
});
