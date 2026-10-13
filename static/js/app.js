// Audion - Client-side Application Controller

let currentJobId = null;
let selectedFile = null;
let originalCleanedText = "";
let voicesList = [];
let eventSource = null;

// DOM Elements
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const selectedFileCard = document.getElementById("selectedFileCard");
const fileNameDisplay = document.getElementById("fileNameDisplay");
const fileSizeDisplay = document.getElementById("fileSizeDisplay");
const btnRemoveFile = document.getElementById("btnRemoveFile");
const btnProcessPDF = document.getElementById("btnProcessPDF");

const voiceSelect = document.getElementById("voiceSelect");
const voiceDescription = document.getElementById("voiceDescription");
const btnPreviewVoice = document.getElementById("btnPreviewVoice");
const previewVoiceLabel = document.getElementById("previewVoiceLabel");
const voicePreviewAudio = document.getElementById("voicePreviewAudio");

const speedSlider = document.getElementById("speedSlider");
const speedValueDisplay = document.getElementById("speedValueDisplay");

const btnToggleFilters = document.getElementById("btnToggleFilters");
const filterOptions = document.getElementById("filterOptions");
const filterChevron = document.getElementById("filterChevron");
const chkFilterHeadersFooters = document.getElementById("chkFilterHeadersFooters");
const chkFilterCitations = document.getElementById("chkFilterCitations");
const chkFilterBookMatter = document.getElementById("chkFilterBookMatter");
const chkUnwrapParagraphs = document.getElementById("chkUnwrapParagraphs");

const uploadSection = document.getElementById("uploadSection");
const progressSection = document.getElementById("progressSection");
const reviewSection = document.getElementById("reviewSection");
const playerSection = document.getElementById("playerSection");

const progressTitle = document.getElementById("progressTitle");
const progressMessage = document.getElementById("progressMessage");
const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");

const metricDuration = document.getElementById("metricDuration");
const metricWords = document.getElementById("metricWords");
const metricPages = document.getElementById("metricPages");
const metricNoise = document.getElementById("metricNoise");
const scriptTextarea = document.getElementById("scriptTextarea");
const btnResetScript = document.getElementById("btnResetScript");
const btnGenerateAudio = document.getElementById("btnGenerateAudio");
const btnBackToUpload = document.getElementById("btnBackToUpload");

// Audio Player elements
const audioElement = document.getElementById("audioElement");
const btnPlayPause = document.getElementById("btnPlayPause");
const playIcon = document.getElementById("playIcon");
const pauseIcon = document.getElementById("pauseIcon");
const audioScrubber = document.getElementById("audioScrubber");
const currentTimeDisplay = document.getElementById("currentTimeDisplay");
const totalTimeDisplay = document.getElementById("totalTimeDisplay");
const btnSkipBack = document.getElementById("btnSkipBack");
const btnSkipForward = document.getElementById("btnSkipForward");
const btnMute = document.getElementById("btnMute");
const volumeIcon = document.getElementById("volumeIcon");
const btnDownloadAudio = document.getElementById("btnDownloadAudio");
const btnRestart = document.getElementById("btnRestart");
const audiobookTitle = document.getElementById("audiobookTitle");
const audiobookVoiceTag = document.getElementById("audiobookVoiceTag");

// Modal elements
const btnOpenModelGuide = document.getElementById("btnOpenModelGuide");
const modelGuideModal = document.getElementById("modelGuideModal");
const btnCloseModelGuide = document.getElementById("btnCloseModelGuide");
const btnDismissGuide = document.getElementById("btnDismissGuide");
const modelsContainer = document.getElementById("modelsContainer");

// Sample file buttons
const btnSampleDigital = document.getElementById("btnSampleDigital");
const btnSampleScanned = document.getElementById("btnSampleScanned");

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
  loadVoices();
  setupEventListeners();
  loadModelsGuide();
});

// Load curated voices
async function loadVoices() {
  try {
    const res = await fetch("/api/voices");
    voicesList = await res.json();
    voiceSelect.innerHTML = "";

    voicesList.forEach((voice) => {
      const opt = document.createElement("option");
      opt.value = voice.id;
      const recStar = voice.recommended ? " ★" : "";
      opt.textContent = `${voice.name} (${voice.accent} ${voice.gender} - ${voice.style})${recStar}`;
      if (voice.recommended && !voiceSelect.value) {
        opt.selected = true;
      }
      voiceSelect.appendChild(opt);
    });

    updateVoiceDescription();
  } catch (err) {
    console.error("Failed to load voices:", err);
  }
}

function updateVoiceDescription() {
  const current = voicesList.find((v) => v.id === voiceSelect.value);
  if (current) {
    voiceDescription.textContent = `${current.description} (${current.accent} Accent, ${current.gender})`;
  }
}

function setupEventListeners() {
  // Voice selection change
  voiceSelect.addEventListener("change", updateVoiceDescription);

  // Speed slider
  speedSlider.addEventListener("input", (e) => {
    speedValueDisplay.textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
  });

  // Filter accordion toggle
  btnToggleFilters.addEventListener("click", () => {
    filterOptions.classList.toggle("hidden");
    filterChevron.classList.toggle("rotate-180");
  });

  // Voice Preview button
  btnPreviewVoice.addEventListener("click", async () => {
    const voiceId = voiceSelect.value;
    if (!voiceId) return;

    previewVoiceLabel.textContent = "Loading...";
    try {
      voicePreviewAudio.src = `/api/voices/${voiceId}/sample`;
      await voicePreviewAudio.play();
      previewVoiceLabel.textContent = "Playing...";
      voicePreviewAudio.onended = () => {
        previewVoiceLabel.textContent = "Preview Voice";
      };
    } catch (err) {
      console.warn("Could not play voice preview:", err);
      previewVoiceLabel.textContent = "Preview Voice";
    }
  });

  // Dropzone drag & drop
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-brand-500", "bg-brand-500/10");
  });

  dropzone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-brand-500", "bg-brand-500/10");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-brand-500", "bg-brand-500/10");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  btnRemoveFile.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    selectedFileCard.classList.add("hidden");
    dropzone.classList.remove("hidden");
    btnProcessPDF.disabled = true;
  });

  // Sample files quick testing
  btnSampleDigital.addEventListener("click", () => loadSamplePDF("sample_digital.pdf"));
  btnSampleScanned.addEventListener("click", () => loadSamplePDF("sample_scanned.pdf"));

  // Process / Extract PDF Button
  btnProcessPDF.addEventListener("click", startExtraction);

  // Script editing & reset
  btnResetScript.addEventListener("click", () => {
    scriptTextarea.value = originalCleanedText;
  });

  btnBackToUpload.addEventListener("click", () => {
    showSection(uploadSection);
  });

  // Generate Audiobook Button
  btnGenerateAudio.addEventListener("click", startGeneration);

  // Audio Player interactions
  setupPlayerEvents();

  // Model guide modal
  btnOpenModelGuide.addEventListener("click", () => modelGuideModal.classList.remove("hidden"));
  btnCloseModelGuide.addEventListener("click", () => modelGuideModal.classList.add("hidden"));
  btnDismissGuide.addEventListener("click", () => modelGuideModal.classList.add("hidden"));
  modelGuideModal.addEventListener("click", (e) => {
    if (e.target === modelGuideModal) modelGuideModal.classList.add("hidden");
  });

  // Restart / Convert Another
  btnRestart.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    selectedFileCard.classList.add("hidden");
    dropzone.classList.remove("hidden");
    btnProcessPDF.disabled = true;
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }
    showSection(uploadSection);
  });
}

function handleFileSelected(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    alert("Please select a PDF file.");
    return;
  }
  selectedFile = file;
  fileNameDisplay.textContent = file.name;
  fileSizeDisplay.textContent = formatBytes(file.size);
  selectedFileCard.classList.remove("hidden");
  dropzone.classList.add("hidden");
  btnProcessPDF.disabled = false;
  if (window.lucide) window.lucide.createIcons();
}

async function loadSamplePDF(filename) {
  try {
    const res = await fetch(`/samples/${filename}`);
    const blob = await res.blob();
    const file = new File([blob], filename, { type: "application/pdf" });
    handleFileSelected(file);
  } catch (err) {
    console.error("Failed to load sample PDF:", err);
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function showSection(section) {
  [uploadSection, progressSection, reviewSection, playerSection].forEach((s) => {
    s.classList.add("hidden");
  });
  section.classList.remove("hidden");
  if (window.lucide) window.lucide.createIcons();
}

// Extraction API call
async function startExtraction() {
  if (!selectedFile) return;

  showSection(progressSection);
  progressTitle.textContent = "Analyzing Document";
  progressMessage.textContent = "Uploading and inspecting PDF layout...";
  progressBar.style.width = "10%";
  progressPercent.textContent = "10%";

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("filter_headers_footers", chkFilterHeadersFooters.checked);
  formData.append("filter_citations", chkFilterCitations.checked);
  formData.append("filter_book_matter", chkFilterBookMatter.checked);
  formData.append("unwrap_paragraphs", chkUnwrapParagraphs.checked);

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    currentJobId = data.job_id;

    // Listen via Server-Sent Events with polling fallback
    listenToJobProgress(currentJobId, (job) => {
      if (job.status === "ready") {
        displayExtractionReview(job);
      } else if (job.status === "failed") {
        alert("Extraction failed: " + (job.error || job.message));
        showSection(uploadSection);
      }
    });
  } catch (err) {
    alert("Error uploading file: " + err.message);
    showSection(uploadSection);
  }
}

function listenToJobProgress(jobId, onCompleteOrFailed) {
  if (eventSource) {
    eventSource.close();
  }

  try {
    eventSource = new EventSource(`/api/jobs/${jobId}/events`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateProgressUI(data);

      if (data.status === "ready" || data.status === "completed" || data.status === "failed") {
        eventSource.close();
        if (onCompleteOrFailed) onCompleteOrFailed(data);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      // Fallback to polling
      pollJobProgress(jobId, onCompleteOrFailed);
    };
  } catch (e) {
    pollJobProgress(jobId, onCompleteOrFailed);
  }
}

async function pollJobProgress(jobId, callback) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) return;
      const data = await res.json();
      updateProgressUI(data);

      if (data.status === "ready" || data.status === "completed" || data.status === "failed") {
        clearInterval(interval);
        if (callback) callback(data);
      }
    } catch (err) {
      console.warn("Polling error:", err);
    }
  }, 1000);
}

function updateProgressUI(job) {
  if (job.progress !== undefined) {
    progressBar.style.width = `${job.progress}%`;
    progressPercent.textContent = `${job.progress}%`;
  }
  if (job.message) {
    progressMessage.textContent = job.message;
  }
}

function displayExtractionReview(job) {
  originalCleanedText = job.cleaned_text || "";
  scriptTextarea.value = originalCleanedText;

  metricDuration.textContent = job.estimated_duration || "~1 min";
  metricWords.textContent = (job.total_words || 0).toLocaleString();

  const ocrLabel = job.ocr_pages_count && job.ocr_pages_count > 0 ? ` (${job.ocr_pages_count} OCR)` : "";
  metricPages.textContent = `${job.total_pages || 1} pgs${ocrLabel}`;

  const noiseCount = (job.stats?.headers_removed || 0) +
                     (job.stats?.footers_removed || 0) +
                     (job.stats?.page_numbers_removed || 0) +
                     (job.stats?.citations_removed || 0) +
                     (job.stats?.book_matter_pages_removed || 0);
  metricNoise.textContent = `${noiseCount} items filtered`;

  showSection(reviewSection);
}

// Generate Audio API call
async function startGeneration() {
  if (!currentJobId) return;

  const editedText = scriptTextarea.value.trim();
  if (!editedText) {
    alert("Script cannot be empty.");
    return;
  }

  showSection(progressSection);
  progressTitle.textContent = "Synthesizing Audiobook";
  progressMessage.textContent = "Connecting to high-fidelity neural speech engine...";
  progressBar.style.width = "5%";
  progressPercent.textContent = "5%";

  const selectedVoice = voiceSelect.value;
  const speed = parseFloat(speedSlider.value);

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: currentJobId,
        text: editedText,
        voice_id: selectedVoice,
        speed: speed,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Generation request failed");
    }

    listenToJobProgress(currentJobId, (job) => {
      if (job.status === "completed") {
        displayPlayer(job);
      } else if (job.status === "failed") {
        alert("Audio generation failed: " + (job.error || job.message));
        showSection(reviewSection);
      }
    });
  } catch (err) {
    alert("Error starting speech synthesis: " + err.message);
    showSection(reviewSection);
  }
}

function displayPlayer(job) {
  const currentVoice = voicesList.find((v) => v.id === voiceSelect.value);
  const voiceName = currentVoice ? currentVoice.name : "Neural Voice";

  audiobookTitle.textContent = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, "") : "Generated Audiobook";
  audiobookVoiceTag.textContent = `Narrated by ${voiceName} • 100% Free Studio Quality`;

  const audioUrl = job.audio_url || `/api/audio/${job.job_id}`;
  audioElement.src = audioUrl;
  btnDownloadAudio.href = audioUrl;
  btnDownloadAudio.download = `${audiobookTitle.textContent}.mp3`;

  showSection(playerSection);
}

function setupPlayerEvents() {
  // Play/Pause
  btnPlayPause.addEventListener("click", () => {
    if (audioElement.paused) {
      audioElement.play();
    } else {
      audioElement.pause();
    }
  });

  audioElement.addEventListener("play", () => {
    playIcon.classList.add("hidden");
    pauseIcon.classList.remove("hidden");
  });

  audioElement.addEventListener("pause", () => {
    playIcon.classList.remove("hidden");
    pauseIcon.classList.add("hidden");
  });

  // Scrubber updates
  audioElement.addEventListener("timeupdate", () => {
    if (!isNaN(audioElement.duration) && audioElement.duration > 0) {
      const pct = (audioElement.currentTime / audioElement.duration) * 100;
      audioScrubber.value = pct;
      currentTimeDisplay.textContent = formatTime(audioElement.currentTime);
    }
  });

  audioElement.addEventListener("loadedmetadata", () => {
    totalTimeDisplay.textContent = formatTime(audioElement.duration);
  });

  audioScrubber.addEventListener("input", (e) => {
    if (!isNaN(audioElement.duration)) {
      const time = (e.target.value / 100) * audioElement.duration;
      audioElement.currentTime = time;
    }
  });

  // Skip 10 seconds
  btnSkipBack.addEventListener("click", () => {
    audioElement.currentTime = Math.max(0, audioElement.currentTime - 10);
  });

  btnSkipForward.addEventListener("click", () => {
    audioElement.currentTime = Math.min(audioElement.duration, audioElement.currentTime + 10);
  });

  // Speed chips
  document.querySelectorAll(".speed-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".speed-btn").forEach((b) => {
        b.classList.remove("active", "bg-brand-500", "text-slate-950", "font-bold");
        b.classList.add("text-slate-400");
      });
      e.target.classList.add("active", "bg-brand-500", "text-slate-950", "font-bold");
      e.target.classList.remove("text-slate-400");
      const rate = parseFloat(e.target.dataset.speed);
      audioElement.playbackRate = rate;
    });
  });

  // Mute toggle
  btnMute.addEventListener("click", () => {
    audioElement.muted = !audioElement.muted;
    if (audioElement.muted) {
      volumeIcon.setAttribute("data-lucide", "volume-x");
    } else {
      volumeIcon.setAttribute("data-lucide", "volume-2");
    }
    if (window.lucide) window.lucide.createIcons();
  });
}

function formatTime(secs) {
  if (isNaN(secs)) return "00:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m < 10 ? "0" : ""}${m}:${s < 10 ? "0" : ""}${s}`;
}

async function loadModelsGuide() {
  try {
    const res = await fetch("/api/config/models");
    const models = await res.json();
    modelsContainer.innerHTML = "";

    models.forEach((m) => {
      const card = document.createElement("div");
      card.className = "p-4 rounded-xl bg-white/5 border border-white/10";

      const badge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Free & active</span>';

      card.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <div class="font-bold text-sm text-white">${m.provider}</div>
          ${badge}
        </div>
        <div class="text-xs text-slate-400 mb-2"><strong>Engine:</strong> ${m.model} &bull; <strong>Sound:</strong> ${m.quality}</div>
        <ul class="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
          ${m.pros.map((p) => `<li>${p}</li>`).join("")}
          ${m.cons.map((c) => `<li class="text-slate-400 italic">${c}</li>`).join("")}
        </ul>
      `;
      modelsContainer.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load models guide:", err);
  }
}

