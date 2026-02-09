# 🧠 NEXUS: Cortex Edition

> **The AI Operating System for Your Digital Life.**  
> _Upgrade your brain. Recall everything. Master your focus._

![NEXUS Version](https://img.shields.io/badge/NEXUS-Cortex%20Edition%20v1.0-00f2ea?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Powered By](https://img.shields.io/badge/Powered%20By-Gemini%202.0%20Flash-orange?style=for-the-badge&logo=google)

---

## 🚀 Overview

**NEXUS** is not just a tool; it's a second brain. It runs in the background, capturing your digital footprint, analyzing it with **Google Gemini 2.0**, and building a searchable **Neural Memory**.

Whether you forgot a specific code snippet from 3 hours ago, need to summarize your day's work, or want to lock in for deep work, NEXUS is your proactive companion.

## ✨ Key Features

### 🧠 **100% Recall**

Never forget anything again. NEXUS indexes everything you see and do.

- **Semantic Search**: "What was that code I wrote about databases?"
- **Visual Memory**: Remembers UI layouts, images, and text.
- **Auto-Summarization**: Ask "What have I been working on?" for a generated report.

### 👁️ **Neural Canvas**

A stunning, real-time visualization of your digital activity.

- **Cyberpunk UI**: Glassmorphism, neon accents, and particle networks.
- **Live Activity Stream**: Watch your digital footprint grow in real-time.

### 🎯 **Focus Mode**

Stop doom-scrolling and get to work.

- **Distraction Blocking**: Visual cues to keep you on track.
- **Productivity Score**: Real-time metric of your cognitive load and focus.

### ⚡ **Performance First**

- **Parallelized Search**: Instant answers using async operations.
- **Robust Architecture**: Self-healing server with automatic retry logic.
- **Safe Mode**: UI continues to function even if dependencies fail.

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10** or higher
- A **Google Gemini API Key** (Get it [here](https://aistudio.google.com/app/apikey))

### One-Click Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/NEXUS.git
    cd NEXUS
    ```

2.  **Run the launcher**:

    ```bash
    ./run.sh
    ```

    _This script automatically creates a virtual environment, installs dependencies, and launches the system._

3.  **Configure API Key**:
    The first time you run it, it might ask for your API key, or you can create a `.env` file manually:
    ```bash
    echo "GOOGLE_API_KEY=your_key_here" > .env
    ```

---

## 🎮 Usage

### Starting NEXUS

Run the command:

```bash
./run.sh
```

Open your browser to: **http://localhost:8000**

### The Interface

1.  **Start Monitoring**: Click the **Start Cortex** button. NEXUS will begin capturing screen activity every 10 seconds.
2.  **Neural Query**: Type in the chat box.
    - _"What app was I using 10 minutes ago?"_
    - _"Summarize the article I just read."_
    - _"How many tabs have I opened?"_
3.  **Focus Mode**: Click **Focus Mode** to toggle the high-contrast productivity interface.

### Stopping

Click **Terminate** in the UI or press `Ctrl+C` in the terminal.

---

## 🔧 Architecture

NEXUS is built on a modern, modular stack:

- **Core**: Python 3.10+
- **Backend**: FastAPI (Async/Await)
- **Database**: SQLite (Metadata) + ChromaDB (Vector Embeddings)
- **Vision/AI**: Google Gemini 2.0 Flash (Multimodal Analysis)
- **Frontend**: Vanilla JS + HTML5 + CSS3 (No framework bloat)
- **Visualization**: Chart.js + HTML5 Canvas (Particle System)

---

## 🔒 Privacy & Data

- **Local First**: All screenshots and database entries are stored locally in the `data/` directory.
- **Encrypted Transmission**: Data is only sent to Google Gemini for analysis over HTTPS and is not trained on (per API terms).
- **You Own It**: Delete the `data/` folder at any time to wipe your memory.

---

## 👨‍💻 Contributing

We welcome contributions! Please fork the repo and submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

> **Built for the Google Gemini Hackathon 2026** 🚀  
> _By Arsh Verma_
