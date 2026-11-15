# -*- coding: utf-8 -*-
__id__ = "delete_from_gallery"
__name__ = "Delete From Gallery"
__description__ = (
    "Adds 'Delete from device' and 'Send and delete' buttons to the attachment picker menu.\n\n"
    "Добавляет кнопки «Удалить с устройства» и «Отправить и удалить» в меню выбора медиа."
)
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.1.5"
__icon__ = "MaxExteraPluginsStickers/23"
__min_version__ = "12.10.6"
__app_version__ = ">=12.10.6"
__sdk_version__ = ">=1.4.3.3"

from typing import Any, List
import json
import time
import threading
import urllib.request

from base_plugin import BasePlugin, MethodHook
from android_utils import run_on_ui_thread, OnClickListener
from client_utils import get_last_fragment
from hook_utils import get_private_field
from ui.settings import Header, Text, Divider
from ui.alert import AlertDialogBuilder
from ui.bulletin import BulletinHelper


DELETE_ITEM_ID = 101
SEND_AND_DELETE_ITEM_ID = 102

CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

DEFAULT_LINKS = {
    "channel_username": "MaxExteraPlugins",
    "channel_url": "https://t.me/MaxExteraPlugins",
    "donate_url": "https://t.me/itNotMax",
    "bug_report_url": "https://t.me/itNotMax",
    "trial_days": 7,
    "header": {
        "ru": "MaxExteraPlugins",
        "en": "MaxExteraPlugins"
    },
    "buttons": [
        {
            "title": {"ru": "Канал автора", "en": "Author's Channel"},
            "icon": "msg_channel",
            "url": "https://t.me/MaxExteraPlugins"
        },
        {
            "title": {"ru": "Поддержать автора", "en": "Support author"},
            "icon": "msg_share",
            "url": "https://t.me/itNotMax"
        },
        {
            "title": {"ru": "Сообщить о баге", "en": "Report a bug"},
            "icon": "msg_help",
            "url": "https://t.me/itNotMax"
        }
    ]
}


class L:
    _T = {
        "delete_from_device": {
            "ru": "Удалить с устройства",
            "en": "Delete from device",
        },
        "send_and_delete": {
            "ru": "Отправить и удалить",
            "en": "Send and delete",
        },
        "no_media_selected": {
            "ru": "Медиа не выбраны",
            "en": "No media selected",
        },
        "no_valid_media": {
            "ru": "Нет подходящих медиа для удаления",
            "en": "No valid media to delete",
        },
        "confirm_delete": {
            "ru": "Подтвердите удаление в системном диалоге",
            "en": "Confirm deletion in system dialog",
        },
        "cannot_get_activity": {
            "ru": "Не удалось получить контекст активности",
            "en": "Cannot get activity context",
        },
        "failed_request_delete": {
            "ru": "Не удалось запросить удаление",
            "en": "Failed to request deletion",
        },
        "deleted_count": {
            "ru": "Удалено файлов: {0}",
            "en": "Deleted {0} file(s)",
        },
        "cannot_delete_files": {
            "ru": "Не удалось удалить файлы",
            "en": "Could not delete files",
        },
        "settings_channel": {
            "ru": "Канал автора",
            "en": "Author's Channel",
        },
        "settings_donate": {
            "ru": "Поддержать автора",
            "en": "Support author",
        },
        "settings_donate_sub": {
            "ru": "Донат на развитие и поддержку плагинов",
            "en": "Donate to support development",
        },
        "settings_bug_report": {
            "ru": "Сообщить о баге",
            "en": "Report a bug",
        },
        "settings_bug_report_sub": {
            "ru": "Написать о проблеме или предложении",
            "en": "Report an issue or suggestion",
        },
        "install_card_title": {
            "ru": "Спасибо за установку!",
            "en": "Thank you for installing!",
        },
        "install_card_msg": {
            "ru": (
                "Надеемся, что плагин будет вам полезен!\n\n"
                "Мы делаем плагины бесплатными и доступными для всех: пожалуйста, поддержите нас подпиской. "
                "Там будут только важные новости, обновления и розыгрыши."
            ),
            "en": (
                "We hope this plugin will be useful to you!\n\n"
                "We keep our plugins free and open for everyone: please support us with a subscription. "
                "We only post key news, updates, and giveaways."
            ),
        },
        "subscribe_btn": {
            "ru": "Подписаться",
            "en": "Subscribe",
        },
        "remind_later_btn": {
            "ru": "Напомнить позже",
            "en": "Remind later",
        },
        "check_sub_btn": {
            "ru": "Проверить подписку",
            "en": "Check subscription",
        },
        "trial_expired_title": {
            "ru": "Пожалуйста, подпишитесь на канал",
            "en": "Please subscribe to the channel",
        },
        "trial_expired_msg": {
            "ru": (
                "Пожалуйста, подпишитесь на наш официальный канал.\n\n"
                "Мы делаем плагины бесплатно, ничего не требуя взамен. "
                "До подписки функции плагина временно приостановлены."
            ),
            "en": (
                "Please subscribe to our official channel.\n\n"
                "We develop plugins for free and ask nothing in return. "
                "Plugin features are paused until you subscribe."
            ),
        },
        "sub_thank_you": {
            "ru": "Спасибо за подписку на наш канал!",
            "en": "Thank you for subscribing to our channel!",
        },
        "sub_thank_you_after_expired": {
            "ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работу!",
            "en": "Thank you for subscribing to our channel!\nThe plugin will continue working!",
        },
        "sub_not_found": {
            "ru": "Подписка не обнаружена. Пожалуйста, подпишитесь на канал.",
            "en": "Subscription not found. Please subscribe to the channel.",
        },
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            cur = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            if cur.startswith("ru") or cur.startswith("uk") or cur.startswith("be"):
                return True
            if cur:
                return False
        except Exception:
            pass

        try:
            from java.util import Locale
            code = str(Locale.getDefault().getLanguage() or "").lower()
            if code.startswith("ru") or code.startswith("uk") or code.startswith("be"):
                return True
        except Exception:
            pass

        return False

    @classmethod
    def g(cls, key: str, *args) -> str:
        lang = "ru" if cls.is_ru() else "en"
        entry = cls._T.get(key)
        if not entry:
            return key
        val = entry.get(lang, entry.get("en", key))
        if args:
            try:
                return val.format(*args)
            except Exception:
                return val
        return val



# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================
class AuthorChannelHelper:
    CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

    DEFAULT_LINKS = {
        "channel_username": "MaxExteraPlugins",
        "channel_url": "https://t.me/MaxExteraPlugins",
        "trial_days": 7,
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Спасибо за установку!", "en": "Thank you for installing!"},
        "install_card_msg": {
            "ru": "Надеемся, что плагин будет вам полезен!\n\nМы делаем плагины бесплатными и доступными для всех: пожалуйста, поддержите нас подпиской. Там будут только важные новости, обновления и розыгрыши.",
            "en": "We hope this plugin will be useful to you!\n\nWe keep our plugins free and open for everyone: please support us with a subscription. We only post key news, updates, and giveaways."
        },
        "subscribe_btn": {"ru": "Подписаться", "en": "Subscribe"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "check_sub_btn": {"ru": "Проверить подписку", "en": "Check subscription"},
        "trial_expired_title": {"ru": "Пожалуйста, подпишитесь на канал", "en": "Please subscribe to the channel"},
        "trial_expired_msg": {
            "ru": "Пожалуйста, подпишитесь на наш официальный канал.\n\nМы делаем плагины бесплатно, ничего не требуя взамен. До подписки функции плагина временно приостановлены.",
            "en": "Please subscribe to our official channel.\n\nWe develop plugins for free and ask nothing in return. Plugin features are paused until you subscribe."
        },
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "sub_thank_you_after_expired": {"ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работу!", "en": "Thank you for subscribing to our channel!\nThe plugin will continue working!"},
        "sub_not_found": {"ru": "Подписка не обнаружена. Пожалуйста, подпишитесь на канал.", "en": "Subscription not found. Please subscribe to the channel."},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            cur = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            if cur.startswith(("ru", "uk", "be")): return True
            if cur: return False
        except Exception:
            pass
        try:
            from java.util import Locale
            code = str(Locale.getDefault().getLanguage() or "").lower()
            if code.startswith(("ru", "uk", "be")): return True
        except Exception:
            pass
        return False

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()
        self._start_subscription_watcher()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                self._check_subscription_change_instant()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def _get_links(self) -> dict:
        raw = self.plugin.get_setting("remote_links_cache", None)
        if raw:
            try:
                import json
                data = json.loads(raw)
                if isinstance(data, dict): return data
            except Exception:
                pass
        return self.DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                import urllib.request, json
                req = urllib.request.Request(self.CONFIG_URL, headers={"User-Agent": "MaxExteraPlugins"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, dict):
                            self.plugin.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception:
                pass
        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            from client_utils import get_last_fragment
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception:
            pass

    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate
            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc: return
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user
            helper_ref = self
            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = self.plugin.get_setting("resolved_channel_id", 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated(): continue
                mc = MessagesController.getInstance(acc)
                if not mc: continue

                if saved_cid:
                    try:
                        from java.lang import Long as JLong
                        c = mc.getChat(JLong(int(saved_cid)))
                        if c is not None:
                            left = bool(getattr(c, "left", True))
                            kicked = bool(getattr(c, "kicked", False))
                            if not left and not kicked: return True
                    except Exception:
                        pass

                try:
                    chat = mc.getUserOrChat(target)
                    if chat is not None:
                        cid = getattr(chat, "id", 0)
                        if cid and not saved_cid:
                            self.plugin.set_setting("resolved_channel_id", int(cid))
                        left = bool(getattr(chat, "left", True))
                        kicked = bool(getattr(chat, "kicked", False))
                        if not left and not kicked: return True
                except Exception:
                    pass

                try:
                    dialogs = mc.allDialogs
                    if dialogs is not None:
                        limit = min(dialogs.size(), 300)
                        for i in range(limit):
                            d = dialogs.get(i)
                            did = getattr(d, "id", 0)
                            if did < 0:
                                from java.lang import Long as JLong
                                c = mc.getChat(JLong(-did))
                                if c is not None:
                                    uname = str(getattr(c, "username", "") or "").lower()
                                    if uname == target:
                                        cid = getattr(c, "id", 0)
                                        if cid and not saved_cid:
                                            self.plugin.set_setting("resolved_channel_id", int(cid))
                                        left = bool(getattr(c, "left", True))
                                        kicked = bool(getattr(c, "kicked", False))
                                        if not left and not kicked: return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def is_allowed(self) -> bool:
        import time
        if self.is_subscribed():
            if not self.plugin.get_setting("was_subscribed", False):
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                self.plugin.set_setting("was_subscribed", True)
                self.plugin.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_exp)
            return True

        if self.plugin.get_setting("was_expired_state", False) or self.plugin.get_setting("was_subscribed", False):
            self.plugin.set_setting("was_subscribed", False)
            self.plugin.set_setting("was_expired_state", True)
            self._show_expired_card()
            return False

        now = time.time()
        install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.plugin.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        self.plugin.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

        # Prevent double-prepending
        if original_items and any(getattr(x, "text", "") == "MaxExteraPlugins" for x in original_items if type(x).__name__ == "Header"):
            return original_items

        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []
        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict): continue
                raw_url = btn.get("url")
                if isinstance(raw_url, dict):
                    keys = [
                        getattr(self.plugin, "id", None),
                        globals().get("__id__", None),
                        globals().get("__name__", None),
                        self.plugin.__class__.__name__
                    ]
                    keys += [k.lower() for k in keys if isinstance(k, str)]
                    resolved_url = ""
                    for k in keys:
                        if k and k in raw_url:
                            resolved_url = str(raw_url[k] or "").strip()
                            if resolved_url:
                                break
                    url = resolved_url
                elif isinstance(raw_url, str):
                    url = raw_url.strip()
                else:
                    url = ""

                if not url: continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if self.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if self.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title: continue
                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(u):
                    return lambda v=None: self._open_url(u, v)

                author_items.append(Text(text=title, icon=icon, on_click=make_click(url)))
        else:
            for k, text_key, icon_name in [
                ("channel_url", "settings_channel", "msg_channel"),
                ("donate_url", "settings_donate", "msg_share"),
                ("bug_report_url", "settings_bug_report", "msg_help")
            ]:
                u = str(links.get(k) or "").strip()
                if u:
                    author_items.append(Text(text=self.tr(text_key), icon=icon_name, on_click=lambda v=None, target_u=u: self._open_url(target_u, v)))

        res = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if self.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)
            res.append(Header(text=hdr_text))
            res.extend(author_items)
            res.append(Divider())

        # Clean original_items by removing any old "Информация" / "Information" category
        cleaned_items = []
        if original_items:
            skipping_info = False
            for item in original_items:
                item_cls = type(item).__name__
                if item_cls == "Header":
                    txt = str(getattr(item, "text", "") or getattr(item, "title", "") or "").lower()
                    if "информ" in txt or "inform" in txt:
                        skipping_info = True
                        continue
                    else:
                        skipping_info = False
                elif skipping_info and item_cls == "Divider":
                    skipping_info = False
                    continue

                if not skipping_info:
                    cleaned_items.append(item)

        res.extend(cleaned_items)
        return res

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _notify_subscribed(self, was_expired=False):
        self.plugin.set_setting("was_subscribed", True)
        from ui.bulletin import BulletinHelper
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(self.tr(msg_key))

    def _check_subscription_change_instant(self):
        try:
            from android_utils import run_on_ui_thread
            cur_sub = self.is_subscribed()
            prev_sub = self._last_known_sub
            if prev_sub is not None and prev_sub != cur_sub:
                self._last_known_sub = cur_sub
                if cur_sub:
                    was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                    self.plugin.set_setting("was_subscribed", True)
                    self.plugin.set_setting("was_expired_state", False)
                    self._dismiss_active_dialog()
                    self._notify_subscribed(was_expired=was_exp)
                else:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._dismiss_active_dialog()
                    self._show_expired_card()
            else:
                self._last_known_sub = cur_sub
        except Exception:
            pass

    def _start_subscription_watcher(self):
        def watcher_loop():
            import time
            from android_utils import run_on_ui_thread
            time.sleep(2.0)
            if self._stopped: return
            self._last_known_sub = self.is_subscribed()

            while not self._stopped:
                try:
                    time.sleep(2.0)
                    if self._stopped: break
                    cur_sub = self.is_subscribed()
                    prev_sub = self._last_known_sub

                    if prev_sub is not None and prev_sub != cur_sub:
                        self._last_known_sub = cur_sub
                        if cur_sub:
                            was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            def on_sub():
                                self._dismiss_active_dialog()
                                self._notify_subscribed(was_expired=was_exp)
                            run_on_ui_thread(on_sub)
                        else:
                            self.plugin.set_setting("was_subscribed", False)
                            self.plugin.set_setting("was_expired_state", True)
                            def on_unsub():
                                self._dismiss_active_dialog()
                                self._show_expired_card()
                            run_on_ui_thread(on_unsub)
                    else:
                        self._last_known_sub = cur_sub
                except Exception:
                    pass
        import threading
        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

    def _check_initial_subscription_flow(self):
        def flow():
            import time
            try:
                now = time.time()
                install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.plugin.set_setting("install_time", install_time)

                is_sub = self.is_subscribed()
                self._last_known_sub = is_sub
                was_sub = bool(self.plugin.get_setting("was_subscribed", False))
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))

                if is_sub:
                    if not was_sub:
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=was_exp)
                    return

                if was_sub or was_exp:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
                    return

                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.plugin.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView
            from android.view import Gravity
            from android.graphics import Typeface
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp
            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(16), dp(24), dp(6))

            size = dp(76)
            iv = BackupImageView(act)
            iv.setRoundRadius(dp(18))
            lp_iv = LinearLayout.LayoutParams(size, size)
            lp_iv.gravity = Gravity.CENTER_HORIZONTAL
            lp_iv.setMargins(0, dp(4), 0, dp(16))
            iv.setLayoutParams(lp_iv)

            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                raw_icon = str(self.icon_sticker)
                if "/" in raw_icon:
                    pack, idx_s = raw_icon.split("/", 1)
                    mdc.setPlaceholderImageByIndex(iv, pack, int(idx_s), "150_150")
            except Exception:
                pass
            layout.addView(iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(None, Typeface.BOLD)
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.setMargins(0, 0, 0, dp(12))
                tt.setLayoutParams(lp_t)
                layout.addView(tt)

            if message_text:
                mt = TextView(act)
                mt.setText(message_text)
                mt.setTextSize(15.0)
                mt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                mt.setLineSpacing(float(dp(3)), 1.0)
                mt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                mt.setLayoutParams(lp_m)
                layout.addView(mt)

            return layout
        except Exception:
            return None

    def _show_welcome_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("install_card_title"), self.tr("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("install_card_title"))
                    b.set_message(self.tr("install_card_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self._notify_subscribed(was_expired=False)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_later(d, w):
                    import time
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_remind_time", time.time())

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("remind_later_btn"), on_later)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                from ui.bulletin import BulletinHelper
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("trial_expired_title"), self.tr("trial_expired_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("trial_expired_title"))
                    b.set_message(self.tr("trial_expired_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            self._notify_subscribed(was_expired=True)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_check(d, w):
                    self._dismiss_active_dialog()
                    if self.is_subscribed():
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(self.tr("sub_not_found"))
                        from android_utils import run_on_ui_thread
                        run_on_ui_thread(self._show_expired_card, 500)

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("check_sub_btn"), on_check)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)


class DeleteFromGalleryPlugin(BasePlugin):

    def on_plugin_load(self):
        self._author_helper = AuthorChannelHelper(self, icon_sticker="MaxExteraPluginsStickers/23")
        self._author_helper.on_load()
        try:
            self._stopped = False
            self._active_dialog = None
            self._last_known_sub = None
            self._load_remote_links_async()
            self._check_initial_subscription_flow()
            self._start_subscription_watcher()
            self._setup_hook()
        except Exception as e:
            self.log(f"[DeleteFromGallery] Hook setup error: {e}")

    def on_app_event(self, event_type):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_event(event_type)
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                self._check_subscription_change_instant()
        except Exception as e:
            self.log(f"[DeleteFromGallery] on_app_event error: {e}")

    def on_plugin_unload(self):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_unload()
        try:
            self._stopped = True
            self._dismiss_active_dialog()
        except Exception:
            pass

    # ============================================================
    # Central Config & Remote Links
    # ============================================================
    def _get_links(self) -> dict:
        raw = self.get_setting("remote_links_cache", None)
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                req = urllib.request.Request(
                    CONFIG_URL,
                    headers={"User-Agent": "MaxExteraPlugins"}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8")
                        data = json.loads(content)
                        if isinstance(data, dict):
                            self.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception as e:
                self.log(f"[DeleteFromGallery] Remote config load note: {e}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception as e:
            self.log(f"[DeleteFromGallery] Open URL error: {e}")

    # ============================================================
    # Settings UI
    # ============================================================
    def create_settings(self):
        try:
            items = self._inner_create_settings()
        except Exception:
            items = []
        if hasattr(self, '_author_helper'):
            return self._author_helper.prepend_settings(items)
        return items

    def _inner_create_settings(self):
        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []

        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict):
                    continue
                url = str(btn.get("url") or "").strip()
                if not url:
                    continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if L.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if L.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title:
                    continue

                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(target_url):
                    return lambda v=None: self._open_url(target_url, v)

                author_items.append(
                    Text(
                        text=title,
                        icon=icon,
                        on_click=make_click(url),
                    )
                )
        else:
            channel_url = str(links.get("channel_url") or "").strip()
            donate_url = str(links.get("donate_url") or "").strip()
            bug_url = str(links.get("bug_report_url") or "").strip()

            if channel_url:
                author_items.append(
                    Text(
                        text=L.g("settings_channel"),
                        icon="msg_channel",
                        on_click=lambda v=None, u=channel_url: self._open_url(u, v),
                    )
                )

            if donate_url:
                author_items.append(
                    Text(
                        text=L.g("settings_donate"),
                        icon="msg_share",
                        on_click=lambda v=None, u=donate_url: self._open_url(u, v),
                    )
                )

            if bug_url:
                author_items.append(
                    Text(
                        text=L.g("settings_bug_report"),
                        icon="msg_help",
                        on_click=lambda v=None, u=bug_url: self._open_url(u, v),
                    )
                )

        items = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if L.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)

            items.append(Header(text=hdr_text))
            items.extend(author_items)
            items.append(Divider())

        return items

    # ============================================================
    # Card Content with Centered Plugin Sticker View
    # ============================================================
    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView
            from android.view import Gravity
            from android.graphics import Typeface
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp

            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(16), dp(24), dp(6))

            # 1. Sticker icon (BackupImageView)
            size = dp(76)
            iv = BackupImageView(act)
            iv.setRoundRadius(dp(18))
            lp_iv = LinearLayout.LayoutParams(size, size)
            lp_iv.gravity = Gravity.CENTER_HORIZONTAL
            lp_iv.setMargins(0, dp(4), 0, dp(16))
            iv.setLayoutParams(lp_iv)

            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                raw_icon = str(__icon__)
                if "/" in raw_icon:
                    pack, idx_s = raw_icon.split("/", 1)
                    mdc.setPlaceholderImageByIndex(iv, pack, int(idx_s), "150_150")
            except Exception as e:
                self.log(f"[DeleteFromGallery] Sticker load note: {e}")

            layout.addView(iv)

            # 2. Title
            if title_text:
                title_tv = TextView(act)
                title_tv.setText(title_text)
                title_tv.setTextSize(19.0)
                title_tv.setTypeface(None, Typeface.BOLD)
                title_tv.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                title_tv.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.setMargins(0, 0, 0, dp(12))
                title_tv.setLayoutParams(lp_t)
                layout.addView(title_tv)

            # 3. Message
            if message_text:
                msg_tv = TextView(act)
                msg_tv.setText(message_text)
                msg_tv.setTextSize(15.0)
                msg_tv.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                msg_tv.setLineSpacing(float(dp(3)), 1.0)
                msg_tv.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                msg_tv.setLayoutParams(lp_m)
                layout.addView(msg_tv)

            return layout
        except Exception as e:
            self.log(f"[DeleteFromGallery] Card content error: {e}")
            return None

    # ============================================================
    # Subscription & Trial Check
    # ============================================================
    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate

            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc:
                return

            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user

            plugin_ref = self

            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                plugin_ref.set_setting("resolved_channel_id", int(cid))

            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed_to_channel(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = links.get("channel_username", "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = self.get_setting("resolved_channel_id", 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated():
                    continue

                mc = MessagesController.getInstance(acc)
                if not mc:
                    continue

                # 1. Check by saved channel ID
                if saved_cid:
                    try:
                        from java.lang import Long as JLong
                        c = mc.getChat(JLong(int(saved_cid)))
                        if c is not None:
                            left = bool(getattr(c, "left", True))
                            kicked = bool(getattr(c, "kicked", False))
                            if not left and not kicked:
                                return True
                    except Exception:
                        pass

                # 2. Check by username lookup in MessagesController
                try:
                    chat = mc.getUserOrChat(target)
                    if chat is not None:
                        cid = getattr(chat, "id", 0)
                        if cid and not saved_cid:
                            self.set_setting("resolved_channel_id", int(cid))
                        left = bool(getattr(chat, "left", True))
                        kicked = bool(getattr(chat, "kicked", False))
                        if not left and not kicked:
                            return True
                except Exception:
                    pass

                # 3. Check dialogs list
                try:
                    dialogs = mc.allDialogs
                    if dialogs is not None:
                        limit = min(dialogs.size(), 300)
                        for i in range(limit):
                            d = dialogs.get(i)
                            did = getattr(d, "id", 0)
                            if did < 0:
                                from java.lang import Long as JLong
                                c = mc.getChat(JLong(-did))
                                if c is not None:
                                    uname = str(getattr(c, "username", "") or "").lower()
                                    if uname == target:
                                        cid = getattr(c, "id", 0)
                                        if cid and not saved_cid:
                                            self.set_setting("resolved_channel_id", int(cid))
                                        left = bool(getattr(c, "left", True))
                                        kicked = bool(getattr(c, "kicked", False))
                                        if not left and not kicked:
                                            return True
                except Exception:
                    pass
        except Exception as e:
            self.log(f"[DeleteFromGallery] is_subscribed error: {e}")
        return False

    def _notify_subscribed(self, was_expired=False):
        self.set_setting("was_subscribed", True)
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(L.g(msg_key))

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _check_subscription_change_instant(self):
        try:
            cur_sub = self.is_subscribed_to_channel()
            prev_sub = self._last_known_sub
            if prev_sub is not None and prev_sub != cur_sub:
                self._last_known_sub = cur_sub
                if cur_sub:
                    was_exp = bool(self.get_setting("was_expired_state", False))
                    self.set_setting("was_subscribed", True)
                    self.set_setting("was_expired_state", False)
                    self._dismiss_active_dialog()
                    self._notify_subscribed(was_expired=was_exp)
                else:
                    self.set_setting("was_subscribed", False)
                    self.set_setting("was_expired_state", True)
                    self._dismiss_active_dialog()
                    self._show_expired_card()
            else:
                self._last_known_sub = cur_sub
        except Exception as e:
            self.log(f"[DeleteFromGallery] instant check note: {e}")

    def _start_subscription_watcher(self):
        def watcher_loop():
            # Initial settling delay
            time.sleep(2.0)
            if self._stopped:
                return

            self._last_known_sub = self.is_subscribed_to_channel()

            while not self._stopped:
                try:
                    time.sleep(2.0)
                    if self._stopped:
                        break

                    cur_sub = self.is_subscribed_to_channel()
                    prev_sub = self._last_known_sub

                    if prev_sub is not None and prev_sub != cur_sub:
                        self.log(f"[DeleteFromGallery] Subscription status changed: {prev_sub} -> {cur_sub}")
                        self._last_known_sub = cur_sub

                        if cur_sub:
                            # Subscribed!
                            was_exp = bool(self.get_setting("was_expired_state", False))
                            self.set_setting("was_subscribed", True)
                            self.set_setting("was_expired_state", False)

                            def on_sub_ui():
                                self._dismiss_active_dialog()
                                self._notify_subscribed(was_expired=was_exp)

                            run_on_ui_thread(on_sub_ui)

                        else:
                            # Unsubscribed / Left channel!
                            self.set_setting("was_subscribed", False)
                            self.set_setting("was_expired_state", True)

                            def on_unsub_ui():
                                self._dismiss_active_dialog()
                                self._show_expired_card()

                            run_on_ui_thread(on_unsub_ui)

                    else:
                        self._last_known_sub = cur_sub

                except Exception as e:
                    self.log(f"[DeleteFromGallery] Watcher loop error: {e}")

        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

    def _check_initial_subscription_flow(self):
        def flow():
            try:
                now = time.time()
                install_time = float(self.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.set_setting("install_time", install_time)

                is_sub = self.is_subscribed_to_channel()
                self._last_known_sub = is_sub
                was_sub = bool(self.get_setting("was_subscribed", False))
                was_expired = bool(self.get_setting("was_expired_state", False))

                if is_sub:
                    if not was_sub:
                        self.set_setting("was_subscribed", True)
                        self.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=was_expired)
                    return

                # User is NOT subscribed
                if was_sub or was_expired:
                    # User had plugin / was subscribed before and left or trial expired!
                    self.set_setting("was_subscribed", False)
                    self.set_setting("was_expired_state", True)
                    self._show_expired_card()
                    return

                # Brand new user within 7 days trial
                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self.set_setting("was_expired_state", True)
                    self._show_expired_card()

            except Exception as e:
                self.log(f"[DeleteFromGallery] Initial flow error: {e}")

        run_on_ui_thread(flow, 1500)

    def is_feature_allowed(self) -> bool:
        if self.is_subscribed_to_channel():
            if not self.get_setting("was_subscribed", False):
                was_expired = bool(self.get_setting("was_expired_state", False))
                self.set_setting("was_subscribed", True)
                self.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_expired)
            return True

        # User is NOT subscribed
        if self.get_setting("was_expired_state", False) or self.get_setting("was_subscribed", False):
            self.set_setting("was_subscribed", False)
            self.set_setting("was_expired_state", True)
            self._show_expired_card()
            return False

        now = time.time()
        install_time = float(self.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        # Trial expired
        self.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def _show_welcome_card(self):
        def show():
            try:
                if self._is_dialog_active():
                    return
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, L.g("install_card_title"), L.g("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(L.g("install_card_title"))
                    b.set_message(L.g("install_card_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed_to_channel():
                            self._notify_subscribed(was_expired=False)
                    run_on_ui_thread(check_after, 3000)

                def on_later(d, w):
                    self._dismiss_active_dialog()
                    self.set_setting("last_remind_time", time.time())

                b.set_positive_button(L.g("subscribe_btn"), on_sub)
                b.set_negative_button(L.g("remind_later_btn"), on_later)
                self._active_dialog = b.show()
            except Exception as e:
                self.log(f"[DeleteFromGallery] Welcome card error: {e}")

        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                if self._is_dialog_active():
                    return
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, L.g("trial_expired_title"), L.g("trial_expired_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(L.g("trial_expired_title"))
                    b.set_message(L.g("trial_expired_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed_to_channel():
                            self.set_setting("was_subscribed", True)
                            self.set_setting("was_expired_state", False)
                            self._notify_subscribed(was_expired=True)
                    run_on_ui_thread(check_after, 3000)

                def on_check(d, w):
                    self._dismiss_active_dialog()
                    if self.is_subscribed_to_channel():
                        self.set_setting("was_subscribed", True)
                        self.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(L.g("sub_not_found"))
                        run_on_ui_thread(self._show_expired_card, 500)

                b.set_positive_button(L.g("subscribe_btn"), on_sub)
                b.set_negative_button(L.g("check_sub_btn"), on_check)
                self._active_dialog = b.show()
            except Exception as e:
                self.log(f"[DeleteFromGallery] Expired card error: {e}")

        run_on_ui_thread(show)

    # ============================================================
    # Hook & Actions
    # ============================================================
    def _setup_hook(self):
        from java.lang import Class, Integer as JInt

        clazz = Class.forName("org.telegram.ui.Components.ChatAttachAlertPhotoLayout")

        try:
            method = clazz.getDeclaredMethod("onSelectedItemsCountChanged", JInt.TYPE)
        except Exception:
            method = clazz.getMethod("onSelectedItemsCountChanged", JInt.TYPE)

        method.setAccessible(True)
        plugin_ref = self

        class MenuHook(MethodHook):
            def after_hooked_method(self, param):
                try:
                    layout = param.thisObject
                    count = param.args[0]
                    if count <= 0:
                        return

                    pa = getattr(layout, "parentAlert", None)
                    if pa is None:
                        return

                    menu = getattr(pa, "selectedMenuItem", None)
                    if menu is None:
                        return

                    existing_ids = set()
                    try:
                        popup = menu.getPopupLayout()
                        if popup is not None:
                            ll = getattr(popup, "linearLayout", None)
                            if ll is not None:
                                for i in range(ll.getChildCount()):
                                    child = ll.getChildAt(i)
                                    existing_ids.add(child.getId())
                    except Exception:
                        pass

                    if DELETE_ITEM_ID not in existing_ids:
                        menu.addSubItem(
                            DELETE_ITEM_ID,
                            plugin_ref._get_icon_res(pa),
                            L.g("delete_from_device")
                        )

                    if SEND_AND_DELETE_ITEM_ID not in existing_ids:
                        menu.addSubItem(
                            SEND_AND_DELETE_ITEM_ID,
                            plugin_ref._get_icon_res(pa),
                            L.g("send_and_delete")
                        )

                    plugin_ref._ensure_click_listener(menu, layout, pa)

                except Exception as e:
                    plugin_ref.log(f"[DeleteFromGallery] Hook error: {e}")

        self.hook_method(method, MenuHook())

    def _ensure_click_listener(self, menu, layout, parent_alert):
        plugin_ref = self

        class ListenerWrapper(OnClickListener):
            def onClick(self, view):
                try:
                    item_id = view.getId()
                    if item_id == DELETE_ITEM_ID:
                        if not plugin_ref.is_feature_allowed():
                            return
                        plugin_ref._perform_delete(layout, parent_alert, send_first=False)
                        return
                    elif item_id == SEND_AND_DELETE_ITEM_ID:
                        if not plugin_ref.is_feature_allowed():
                            return
                        plugin_ref._perform_delete(layout, parent_alert, send_first=True)
                        return
                except Exception as e:
                    plugin_ref.log(f"[DeleteFromGallery] Item click error: {e}")

                orig = getattr(menu, "_orig_delegate_listener", None)
                if orig is not None:
                    orig.onClick(view)

        try:
            popup = menu.getPopupLayout()
            if popup is None:
                return

            ll = getattr(popup, "linearLayout", None)
            if ll is None:
                return

            for i in range(ll.getChildCount()):
                child = ll.getChildAt(i)
                cid = child.getId()
                if cid in (DELETE_ITEM_ID, SEND_AND_DELETE_ITEM_ID):
                    if not getattr(child, "_wrapped_click", False):
                        child.setOnClickListener(ListenerWrapper())
                        child._wrapped_click = True
        except Exception as e:
            self.log(f"[DeleteFromGallery] Click listener error: {e}")

    def _get_icon_res(self, parent_alert):
        try:
            from org.telegram.messenger import R
            return R.drawable.msg_delete
        except Exception:
            return 0

    def _get_activity(self, parent_alert):
        try:
            base_frag = getattr(parent_alert, "baseFragment", None)
            if base_frag is not None:
                act = base_frag.getParentActivity()
                if act is not None:
                    return act
        except Exception:
            pass

        frag = get_last_fragment()
        if frag is not None:
            act = frag.getParentActivity()
            if act is not None:
                return act

        return None

    def _clean_media_controller_albums(self, valid):
        try:
            from org.telegram.messenger import MediaController
            albums = getattr(MediaController, "allMediaAlbums", None)
            if albums is None:
                return

            valid_ids = set()
            for entry in valid:
                try:
                    valid_ids.add(int(entry.imageId))
                except Exception:
                    pass

            for album_idx in range(albums.size()):
                album = albums.get(album_idx)
                photos = getattr(album, "photos", None)
                if photos is None:
                    continue

                for photo_idx in range(photos.size() - 1, -1, -1):
                    p = photos.get(photo_idx)
                    try:
                        if int(p.imageId) in valid_ids:
                            photos.remove(photo_idx)
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"[DeleteFromGallery] Album cleanup error: {e}")

    def _send_media(self, parent_alert):
        try:
            photo_layout = getattr(parent_alert, "photoLayout", None)
            if photo_layout is not None:
                method = photo_layout.getClass().getDeclaredMethod("sendSelectedPhotos", [False.__class__] if hasattr(False, '__class__') else [])
            parent_alert.sendPressed(True, 0)
        except Exception:
            try:
                parent_alert.sendPressed(True, 0)
            except Exception as e:
                self.log(f"[DeleteFromGallery] Send media error: {e}")

    def _clear_selection(self, layout, parent_alert, valid):
        def do_clear():
            try:
                from org.telegram.ui.Components import ChatAttachAlertPhotoLayout
                sel_photos = getattr(ChatAttachAlertPhotoLayout, "selectedPhotos", None)
                sel_order = getattr(ChatAttachAlertPhotoLayout, "selectedPhotosOrder", None)

                for entry in valid:
                    try:
                        if sel_photos is not None:
                            sel_photos.remove(entry.imageId)
                        if sel_order is not None:
                            sel_order.remove(entry.imageId)
                    except Exception:
                        pass

                try:
                    adapter = get_private_field(layout, "adapter")
                    if adapter is not None:
                        adapter.notifyDataSetChanged()
                except Exception:
                    pass

                try:
                    parent_alert.updateCountButton(2)
                except Exception:
                    pass

            except Exception as e:
                self.log(f"[DeleteFromGallery] Clear selection error: {e}")

        run_on_ui_thread(do_clear)

    def _execute_media_deletion(self, activity, resolver, uris, valid, sdk):
        if sdk >= 30:
            try:
                from android.provider import MediaStore
                pi = MediaStore.createDeleteRequest(resolver, uris)
                if activity is not None:
                    activity.startIntentSenderForResult(pi.getIntentSender(), 110, None, 0, 0, 0)
                    BulletinHelper.show_info(L.g("confirm_delete"))
                else:
                    BulletinHelper.show_error(L.g("cannot_get_activity"))
            except Exception as e:
                self.log(f"[DeleteFromGallery] createDeleteRequest error: {e}")
                BulletinHelper.show_error(L.g("failed_request_delete"))
        else:
            deleted = 0
            for i in range(uris.size()):
                try:
                    if resolver.delete(uris.get(i), None, None) > 0:
                        deleted += 1
                except Exception as e:
                    self.log(f"[DeleteFromGallery] ContentResolver.delete error: {e}")

            if deleted < len(valid):
                for entry in valid:
                    try:
                        path = str(entry.path) if entry.path is not None else None
                        if path is None:
                            continue
                        from java.io import File as JFile
                        f = JFile(path)
                        if f.exists() and f.delete():
                            deleted += 1
                    except Exception:
                        pass

            if deleted > 0:
                BulletinHelper.show_success(L.g("deleted_count", deleted))
            else:
                BulletinHelper.show_error(L.g("cannot_delete_files"))

        self._clean_media_controller_albums(valid)

    def _perform_delete(self, layout, parent_alert, send_first=False):
        from org.telegram.ui.Components import ChatAttachAlertPhotoLayout
        from org.telegram.messenger import ApplicationLoader
        from android.provider import MediaStore
        from android.content import ContentUris
        from android.os import Build
        from java.util import ArrayList as JArrayList

        menu = getattr(parent_alert, "selectedMenuItem", None)
        if menu is not None:
            try:
                menu.closeSubMenu()
            except Exception:
                pass

        sel_photos = getattr(ChatAttachAlertPhotoLayout, "selectedPhotos", None)
        if sel_photos is None or sel_photos.isEmpty():
            BulletinHelper.show_error(L.g("no_media_selected"))
            return

        entries = []
        it = sel_photos.values().iterator()
        while it.hasNext():
            entries.append(it.next())

        ctx = ApplicationLoader.applicationContext
        resolver = ctx.getContentResolver()
        sdk = Build.VERSION.SDK_INT

        uris = JArrayList()
        valid = []

        for entry in entries:
            try:
                img_id = int(entry.imageId)
                if img_id <= 0:
                    continue
                base = MediaStore.Video.Media.EXTERNAL_CONTENT_URI if entry.isVideo else MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                uris.add(ContentUris.withAppendedId(base, img_id))
                valid.append(entry)
            except Exception as e:
                self.log(f"[DeleteFromGallery] URI build error: {e}")

        if uris.isEmpty():
            BulletinHelper.show_error(L.g("no_valid_media"))
            return

        activity = self._get_activity(parent_alert)

        if send_first:
            self._send_media(parent_alert)

            def do_delayed_delete():
                self._execute_media_deletion(activity, resolver, uris, valid, sdk)

            try:
                run_on_ui_thread(do_delayed_delete, 400)
            except Exception:
                import threading
                threading.Timer(0.4, lambda: run_on_ui_thread(do_delayed_delete)).start()
        else:
            self._clear_selection(layout, parent_alert, valid)
            self._execute_media_deletion(activity, resolver, uris, valid, sdk)


# __DEX_BEGIN__
# PLACEHOLDER
# __DEX_END__
