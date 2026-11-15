# delete_from_gallery

<p align="center">
  <b>English version</b> | <a href="README.md"><b>Русская версия</b></a>
</p>

<p align="center">
  <a href="https://github.com/MaxExteraPlugins/delete_from_gallery/releases/latest">
    <img src="https://img.shields.io/github/v/release/MaxExteraPlugins/delete_from_gallery?style=flat-square&color=blue" alt="Latest Release"/>
  </a>
  <img src="https://img.shields.io/badge/exteraGram-%3E%3D12.10.6-orange?style=flat-square" alt="exteraGram"/>
  <img src="https://img.shields.io/badge/AyuGram-%3E%3D12.10.6-blueviolet?style=flat-square" alt="AyuGram"/>
  <a href="https://t.me/MaxExteraPlugins">
    <img src="https://img.shields.io/badge/Telegram-@MaxExteraPlugins-2CA5E0?style=flat-square&logo=telegram" alt="Telegram Channel"/>
  </a>
</p>

---

## 📖 Overview

A plugin for **exteraGram** and **AyuGram** clients that enhances the native attachment picker with convenient media deletion actions:

* **"Delete from device"** — permanently deletes selected photos and videos from your local device gallery directly within Telegram.
* **"Send and delete"** — sends chosen photos/videos to the chat and immediately removes them from your phone storage to save disk space.

---

## ⚙️ Features

* **Native Attachment Menu Integration:** Adds custom actions directly to the selection submenu in the photo/video picker.
* **Plugin Settings:** Quick access to the official updates channel and support/donation links.
* **Modern Android Support:** Fully compatible with Android 11+ Scoped Storage (MediaStore delete requests).

---

## 📥 Installation

1. Navigate to the [**Releases**](https://github.com/MaxExteraPlugins/delete_from_gallery/releases/latest) section.
2. Download the `delete_from_gallery_vX.X.X.plugin` file.
3. Send it to Telegram (e.g. Saved Messages) or open it using a file manager in exteraGram / AyuGram.
4. Tap the file in Telegram and select **"Install Plugin"**.

---

## 📋 Compatibility

* **exteraGram:** `>= 12.10.6`
* **AyuGram:** `>= 12.10.6`
* **Plugin SDK:** `>= 1.4.3.3`

---

## 🛠 Building from Source

To build the plugin manually, ensure Android SDK (`d8`, `android.jar`) and JDK 8+ are available:

```cmd
# Run plugin build:
build.bat
```

The script compiles the Java hook, converts it into DEX bytecode using `d8`, compresses and base64 encodes it, and bundles everything into a runnable `.plugin` file.

---

## 👨‍💻 Credits & Links

* **Author:** [@itNotMax](https://t.me/itNotMax)
* **Official Channel:** [@MaxExteraPlugins](https://t.me/MaxExteraPlugins)
* **Support the author:** [@itNotMax](https://t.me/itNotMax)
