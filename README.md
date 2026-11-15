# Delete From Gallery

<p align="center">
  <img src="https://raw.githubusercontent.com/MaxExteraPlugins/.github/main/assets/banner.png" alt="Delete From Gallery" width="100%" onerror="this.style.display='none'"/>
</p>

<p align="center">
  <a href="https://github.com/MaxExteraPlugins/delete_from_gallery/releases/latest">
    <img src="https://img.shields.io/github/v/release/MaxExteraPlugins/delete_from_gallery?style=flat-square&color=blue" alt="Release"/>
  </a>
  <img src="https://img.shields.io/badge/exteraGram-%3E%3D12.10.6-orange?style=flat-square" alt="exteraGram Version"/>
  <img src="https://img.shields.io/badge/AyuGram-%3E%3D12.10.6-blueviolet?style=flat-square" alt="AyuGram Version"/>
  <a href="https://t.me/MaxExteraPlugins">
    <img src="https://img.shields.io/badge/Telegram-@MaxExteraPlugins-2CA5E0?style=flat-square&logo=telegram" alt="Telegram Channel"/>
  </a>
</p>

---

## 📖 Описание / Description

**RU:**  
Плагин для **exteraGram** и **AyuGram**, который добавляет в меню выбора вложений (attachment picker) удобные опции:
* **«Удалить с устройства»** — навсегда удаляет выбранные фото и видео из галереи устройства прямо из Telegram.
* **«Отправить и удалить»** — отправляет медиафайлы в чат и сразу удаляет их из локального хранилища устройства, экономя память.

**EN:**  
Plugin for **exteraGram** and **AyuGram** that introduces convenient actions into the media attachment picker:
* **"Delete from device"** — permanently removes selected photos/videos from device gallery directly within Telegram.
* **"Send and delete"** — sends chosen media to the chat and immediately wipes them from local device storage.

---

## 📥 Установка / Installation

1. Перейдите во вкладку [**Releases**](https://github.com/MaxExteraPlugins/delete_from_gallery/releases/latest).
2. Скачайте файл `delete_from_gallery.plugin`.
3. Отправьте файл в Telegram (например, в «Избранное») или откройте его через проводник в exteraGram / AyuGram.
4. Нажмите на файл и подтвердите установку: **Установить плагин**.

---

## ⚙️ Совместимость / Compatibility

* **exteraGram:** `>= 12.10.6`
* **AyuGram:** `>= 12.10.6`
* **Plugin SDK:** `>= 1.4.3.3`

---

## 🛠 Сборка из исходников / Build from Source

Проект использует систему сборки **ETG PluginSystem**:

```cmd
# Запуск сборки плагина:
build.bat
```

Скрипт скомпилирует Java-хук (`code/java.java`), сконвертирует его в DEX через `d8`, сожмет и внедрит полезную нагрузку в `code/python.py`, сгенерировав готовый `delete_from_gallery.plugin`.

---

## 👨‍💻 Авторы / Credits

* **Автор:** [@itNotMax](https://t.me/itNotMax)
* **Канал с плагинами:** [@MaxExteraPlugins](https://t.me/MaxExteraPlugins)
