# Streamlit Community Cloud Deployment Guide

This document details the step-by-step process to deploy the **Cricbuzz LiveStats Platform** on Streamlit Community Cloud (share.streamlit.io).

---

## 1. Prerequisites
* A GitHub account with the code pushed to: `https://github.com/YashwanthNavari/-Cricbuzz-LiveStats` (Completed ✅).
* A free [Streamlit Share](https://share.streamlit.io) account connected to your GitHub account.
* A valid Cricbuzz RapidAPI Key (`RAPIDAPI_KEY`).

---

## 2. Choosing a Relational Database

Streamlit Community Cloud runs in ephemeral Docker containers. The local filesystems are temporary—when the app goes to sleep or restarts, any writes to the local SQLite database file (`cricbuzz_db.sqlite`) will be lost.

### Option A: Local SQLite (Fast & Ephemeral)
* **Best for:** Fast testing, demonstrations, or homework submissions.
* **Behavior:** Works instantly, but data resets whenever the app reboots or sleeps.
* **Secrets String:** `DATABASE_URL = "sqlite:///cricbuzz_db.sqlite"`

### Option B: Cloud PostgreSQL (Recommended & Persistent)
* **Best for:** Production dashboards, permanent data tracking, and multi-user access.
* **Hosting Options:** Spin up a free PostgreSQL database tier on one of the following clouds:
  * **[Neon.tech](https://neon.tech/)** (Free serverless Postgres tier)
  * **[Supabase.com](https://supabase.com/)** (Free managed Postgres tier)
* **Secrets String:** `DATABASE_URL = "postgresql://username:password@your-database-host:5432/dbname?sslmode=require"`

---

## 3. Step-by-Step Deployment Steps

1. **Log In to Streamlit Cloud:**
   Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your connected GitHub credentials.

2. **Deploy a New App:**
   Click the **"New app"** button in the top-right corner.

3. **Configure Repository Settings:**
   Fill in your repository information:
   * **Repository:** `YashwanthNavari/-Cricbuzz-LiveStats`
   * **Branch:** `main`
   * **Main file path:** `app.py`
   * **App URL:** (Optional) Customize your subdomain, e.g. `cricbuzz-livestats.streamlit.app`

4. **Add Environment Secrets (Crucial 🔑):**
   Before clicking deploy, expand the **"Advanced settings..."** link at the bottom. Under **Secrets (TOML format)**, copy and paste the following config, replacing placeholders with your keys:
   ```toml
   RAPIDAPI_KEY = "your_real_rapidapi_key_here"
   RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
   DATABASE_URL = "sqlite:///cricbuzz_db.sqlite"
   ```
   *Note: If you are using a cloud database, replace the SQLite string with your PostgreSQL connection URL.*

5. **Launch the App:**
   Click **"Deploy!"** Streamlit will automatically read your `requirements.txt`, install dependencies, inject the secrets, initialize the SQL schema (via the migrator inside `init_db()`), and launch the app in 1–2 minutes.
