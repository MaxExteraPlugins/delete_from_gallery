# Delete From Gallery

<p align="center">
  <a href="README_EN.md"><b>English version</b></a> | <b>Русская версия</b>
</p>

<p align="center">
  <a href="https://github.com/MaxExteraPlugins/DeleteFromGallery/releases/latest">
    <img src="https://img.shields.io/github/v/release/MaxExteraPlugins/DeleteFromGallery?style=flat-square&color=blue" alt="Версия релиза"/>
  </a>
  <img src="https://img.shields.io/badge/exteraGram-%3E%3D12.10.6-orange?style=flat-square" alt="exteraGram"/>
  <img src="https://img.shields.io/badge/AyuGram-%3E%3D12.10.6-blueviolet?style=flat-square" alt="AyuGram"/>
  <a href="https://t.me/MaxExteraPlugins">
    <img src="https://img.shields.io/badge/Telegram-@MaxExteraPlugins-2CA5E0?style=flat-square&logo=telegram" alt="Telegram канал"/>
  </a>
</p>

---

## 📖 Описание

Плагин для клиентов **exteraGram** и **AyuGram**, который расширяет стандартное меню выбора вложений (attachment picker) и добавляет функции быстрого удаления медиафайлов:

* **«Удалить с устройства»** — навсегда удаляет выбранные фото и видео из локальной галереи вашего телефона прямо из меню Telegram.
* **«Отправить и удалить»** — отправляет выбранные фото/видео в чат и сразу удаляет их из локального хранилища устройства, экономя память смартфона.

---

## ⚙️ Возможности и настройки

* **Интеграция в нативное меню выбора фото/видео:** Кнопки аккуратно встраиваются в выпадающее меню выбранных файлов.
* **Настройки плагина:** В настройках плагина доступен быстрый переход в официальный канал обновлений и ссылка на поддержку разработки.
* **Поддержка актуальных версий Android:** Корректно запрашивает системные разрешения через Android MediaStore (включая Android 11+ Scoped Storage).

---

## 📥 Установка

1. Перейдите во вкладку [**Releases**](https://github.com/MaxExteraPlugins/DeleteFromGallery/releases/latest).
2. Скачайте файл плагина формата `delete_from_gallery_vX.X.X.plugin`.
3. Отправьте файл в Telegram (в «Избранное») или откройте его через проводник в exteraGram / AyuGram.
4. Нажмите на сообщение с плагином и выберите **«Установить плагин»**.

---

## 📋 Совместимость

* **exteraGram:** `>= 12.10.6`
* **AyuGram:** `>= 12.10.6`
* **Plugin SDK:** `>= 1.4.3.3`

---

## 🛠 Сборка из исходников

Для самостоятельной сборки плагина требуется установленный Android SDK (`d8`, `android.jar`) и JDK 8+:

```cmd
# Запуск сборки плагина:
build.bat
```

Скрипт скомпилирует Java-хук, преобразует его в DEX-байткод через утилиту `d8`, сожмет алгоритмом zlib, закодирует в base64 и соберет готовый исполняемый файл `.plugin`.

---

## 👨‍💻 Авторство и ссылки

* **Автор:** [@itNotMax](https://t.me/itNotMax)
* **Официальный канал плагинов:** [@MaxExteraPlugins](https://t.me/MaxExteraPlugins)
* **Поддержать автора:** [@itNotMax](https://t.me/itNotMax)
