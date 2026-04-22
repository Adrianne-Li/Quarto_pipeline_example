# PySAL Quarto Dashboard

A reproducible and automated pipeline for collecting, processing, and visualizing PySAL ecosystem metrics using Python, Quarto, and GitHub Actions.


## Repository Structure

```text
pysal-quarto-site/
│
├── _quarto.yml                  # Quarto project configuration
│
├── index.qmd                   # Landing page
├── snapshot.qmd                # Static (archived) visualization
├── latest.qmd                  # Auto-updated visualization
│
├── styles.css                  # Global styling
│
├── js/
│   └── pysal-rose.js           # D3.js rose plot renderer
│
├── data/
│   ├── pysal_metrics_snapshot.json   # Fixed snapshot dataset
│   └── pysal_metrics_latest.json     # Auto-refreshed dataset
│
├── scripts/
│   └── build_pysal_metrics.py # Data pipeline (API → JSON)
│
├── requirements.txt           # Python dependencies
├── .nojekyll                  # Required for GitHub Pages static serving
│
└── .github/
    └── workflows/
        └── publish.yml        # CI/CD pipeline (build + deploy)
```


## Project Overview

This project builds an automated dashboard to track PySAL module performance across:

* PyPI downloads
* Conda downloads
* GitHub activity (stars, forks, contributors)
* Package age

The pipeline is fully automated and deployed via GitHub Pages.


## ⚙️ Pipeline Summary

```text
scripts → data → quarto → _site → GitHub Pages
```

* **Python (`scripts/`)**: fetches and processes data
* **JSON (`data/`)**: stores structured metrics
* **Quarto (`.qmd`)**: renders pages
* **GitHub Actions**: automates updates and deployment


## Pages

* `/` — Overview
* `/snapshot.html` — Static dataset view
* `/latest.html` — Auto-updated live view


##  Tech Stack

* Python
* Quarto
* D3.js
* GitHub Actions
* GitHub Pages


##  Author

Zhuyin Li
University of Chicago, CSDS

---
