# -*- coding: utf-8 -*-
__id__ = "delete_from_gallery"
__name__ = "Delete From Gallery"
__description__ = (
    "Adds 'Delete from device' and 'Send and delete' buttons to the attachment picker menu.\n\n"
    "Добавляет кнопки «Удалить с устройства» и «Отправить и удалить» в меню выбора медиа."
)
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.2.2"
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
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Подпишитесь на канал", "en": "Subscribe to channel"},
        "install_card_msg": {
            "ru": (
                "Мы делаем плагины бесплатными и доступными для всех: пожалуйста, "
                "поддержите нас подпиской на официальный канал @MaxExteraPlugins.\n\n"
                "Там публикуются обновления, важные новости и анонсы новых плагинов."
            ),
            "en": (
                "We keep our plugins free and accessible for everyone: please "
                "support us by subscribing to our official channel @MaxExteraPlugins.\n\n"
                "Updates, news, and new plugin announcements are published there."
            )
        },
        "open_channel_btn": {"ru": "Перейти на канал", "en": "Open channel"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "never_show_btn": {"ru": "Больше не показывать", "en": "Don't show again"},
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            lang = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            return lang in ("ru", "be", "uk", "kk")
        except Exception:
            return True

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                if self.is_subscribed() and not self.plugin.get_setting("was_subscribed", False):
                    self.plugin.set_setting("was_subscribed", True)
                    self._dismiss_active_dialog()
                    self._notify_subscribed()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def is_allowed(self) -> bool:
        return True

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
                            for a in range(UserConfig.MAX_ACCOUNT_COUNT):
                                try:
                                    if UserConfig.getInstance(a).isClientActivated():
                                        MessagesController.getInstance(a).putChats(chats, False)
                                except Exception:
                                    pass
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController, MessagesStorage
            from java.lang import Long as JLong
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = int(self.plugin.get_setting("resolved_channel_id", 0) or 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                try:
                    uconf = UserConfig.getInstance(acc)
                    if not uconf.isClientActivated():
                        continue

                    mc = MessagesController.getInstance(acc)
                    storage = MessagesStorage.getInstance(acc)

                    # 1. In-memory check by resolved_channel_id
                    if saved_cid and mc is not None:
                        try:
                            c = mc.getChat(JLong(saved_cid))
                            if c is not None:
                                left = bool(getattr(c, "left", True))
                                kicked = bool(getattr(c, "kicked", False))
                                if not left and not kicked:
                                    return True
                        except Exception:
                            pass

                    # 2. In-memory check by username
                    if mc is not None:
                        try:
                            chat = mc.getUserOrChat(target)
                            if chat is not None:
                                cid = int(getattr(chat, "id", 0) or 0)
                                if cid and not saved_cid:
                                    saved_cid = cid
                                    self.plugin.set_setting("resolved_channel_id", cid)
                                left = bool(getattr(chat, "left", True))
                                kicked = bool(getattr(chat, "kicked", False))
                                if not left and not kicked:
                                    return True
                        except Exception:
                            pass

                    # 3. In-memory dialogs check
                    if mc is not None:
                        try:
                            dialog_lists = []
                            d_chan = getattr(mc, "dialogsChannelsOnly", None)
                            if d_chan is not None and d_chan.size() > 0:
                                dialog_lists.append(d_chan)
                            d_all = getattr(mc, "allDialogs", None)
                            if d_all is not None and d_all.size() > 0:
                                dialog_lists.append(d_all)

                            for d_list in dialog_lists:
                                limit = min(d_list.size(), 300)
                                for i in range(limit):
                                    d = d_list.get(i)
                                    did = getattr(d, "id", 0)
                                    if did < 0:
                                        cid = -did
                                        if saved_cid and cid == saved_cid:
                                            c = mc.getChat(JLong(cid))
                                            if c is not None:
                                                left = bool(getattr(c, "left", True))
                                                kicked = bool(getattr(c, "kicked", False))
                                                if not left and not kicked:
                                                    return True
                                        else:
                                            c = mc.getChat(JLong(cid))
                                            if c is not None:
                                                uname = str(getattr(c, "username", "") or "").lower()
                                                if uname == target:
                                                    if not saved_cid:
                                                        saved_cid = cid
                                                        self.plugin.set_setting("resolved_channel_id", cid)
                                                    left = bool(getattr(c, "left", True))
                                                    kicked = bool(getattr(c, "kicked", False))
                                                    if not left and not kicked:
                                                        return True
                        except Exception:
                            pass

                    # 4. Storage check (SQLite on disk)
                    if storage is not None:
                        if saved_cid:
                            try:
                                if storage.containsLocalDialog(JLong(-saved_cid)):
                                    c_sync = storage.getChatSync(JLong(saved_cid))
                                    if c_sync is not None:
                                        left = bool(getattr(c_sync, "left", True))
                                        kicked = bool(getattr(c_sync, "kicked", False))
                                        if not left and not kicked:
                                            return True
                                    else:
                                        return True
                            except Exception:
                                pass

                        try:
                            db = storage.getDatabase()
                            if db is not None:
                                if saved_cid:
                                    try:
                                        cur = db.queryFinalized("SELECT did FROM dialogs WHERE did = ?", [JLong(-saved_cid)])
                                        if cur is not None:
                                            has_row = bool(cur.next())
                                            cur.dispose()
                                            if has_row:
                                                return True
                                    except Exception:
                                        pass

                                try:
                                    cur = db.queryFinalized("SELECT uid, name FROM chats WHERE LOWER(name) LIKE ?", ["%" + target + "%"])
                                    if cur is not None:
                                        while cur.next():
                                            c_id = cur.longValue(0)
                                            if c_id > 0:
                                                if not saved_cid:
                                                    saved_cid = int(c_id)
                                                    self.plugin.set_setting("resolved_channel_id", saved_cid)
                                                cur_d = db.queryFinalized("SELECT did FROM dialogs WHERE did = ?", [JLong(-c_id)])
                                                if cur_d is not None:
                                                    in_dlg = bool(cur_d.next())
                                                    cur_d.dispose()
                                                    if in_dlg:
                                                        cur.dispose()
                                                        return True
                                        cur.dispose()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

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

    def _notify_subscribed(self):
        try:
            from ui.bulletin import BulletinHelper
            BulletinHelper.show_success(self.tr("sub_thank_you"))
        except Exception:
            pass

    def _check_initial_subscription_flow(self):
        def flow():
            try:
                if self.plugin.get_setting("never_show_sub_prompt", False):
                    return

                current_ver = str(getattr(self.plugin, "__version__", globals().get("__version__", "1.0.0")) or "1.0.0")
                last_prompted_ver = self.plugin.get_setting("last_prompted_version", None)

                # Only show on install (last_prompted_ver is None) or update (last_prompted_ver != current_ver)
                if last_prompted_ver is not None and str(last_prompted_ver) == current_ver:
                    return

                if self.is_subscribed():
                    self.plugin.set_setting("last_prompted_version", current_ver)
                    self.plugin.set_setting("was_subscribed", True)
                    return

                self._show_subscription_prompt(current_ver)
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView, ImageView
            from android.view import Gravity
            from org.telegram.messenger import AndroidUtilities
            from org.telegram.ui.ActionBar import Theme
            from client_utils import create_sticker_drawable

            dp = AndroidUtilities.dp

            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(20), dp(24), dp(10))

            sticker_drawable = None
            if self.icon_sticker:
                try:
                    sticker_drawable = create_sticker_drawable(self.icon_sticker, dp(120), dp(120))
                except Exception:
                    pass

            if sticker_drawable is not None:
                iv = ImageView(act)
                iv.setImageDrawable(sticker_drawable)
                lp_iv = LinearLayout.LayoutParams(dp(120), dp(120))
                lp_iv.gravity = Gravity.CENTER_HORIZONTAL
                lp_iv.bottomMargin = dp(14)
                layout.addView(iv, lp_iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(AndroidUtilities.bold())
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.bottomMargin = dp(8)
                layout.addView(tt, lp_t)

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

    def _show_subscription_prompt(self, current_ver: str):
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

                def on_open_channel(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_prompted_version", current_ver)
                    self._open_url(url)

                def on_remind_later(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_prompted_version", current_ver)

                def on_never_show(dialog, which):
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("never_show_sub_prompt", True)
                    self.plugin.set_setting("last_prompted_version", current_ver)

                b.set_positive_button(self.tr("open_channel_btn"), on_open_channel)
                b.set_neutral_button(self.tr("remind_later_btn"), on_remind_later)
                b.set_negative_button(self.tr("never_show_btn"), on_never_show)

                def on_dismiss(builder):
                    self.plugin.set_setting("last_prompted_version", current_ver)
                try:
                    b.set_on_dismiss_listener(on_dismiss)
                except Exception:
                    pass

                self._active_dialog = b.show()
                self.plugin.set_setting("last_prompted_version", current_ver)
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)


        class CountHook(MethodHook):
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

                    plugin_ref._add_menu_items_if_needed(menu, layout, pa)
                except BaseException as e:
                    plugin_ref.log(f"[DeleteFromGallery] CountHook error: {e}")

        self.hook_method(count_method, CountHook())

        try:
            click_method = clazz.getDeclaredMethod("onMenuItemClick", JInt.TYPE)
            click_method.setAccessible(True)

            class ClickHook(MethodHook):
                def before_hooked_method(self, param):
                    try:
                        item_id = int(param.args[0])
                        layout = param.thisObject
                        pa = getattr(layout, "parentAlert", None)
                        if item_id == DELETE_ITEM_ID:
                            param.setResult(None)
                            plugin_ref._on_action(layout, pa, send_first=False)
                        elif item_id == SEND_AND_DELETE_ITEM_ID:
                            param.setResult(None)
                            plugin_ref._on_action(layout, pa, send_first=True)
                    except BaseException as e:
                        plugin_ref.log(f"[DeleteFromGallery] ClickHook error: {e}")

            self.hook_method(click_method, ClickHook())
        except BaseException as e:
            plugin_ref.log(f"[DeleteFromGallery] onMenuItemClick hook error: {e}")

    def _has_sub_item(self, menu, item_id: int) -> bool:
        try:
            if menu.hasSubItem(item_id):
                return True
        except BaseException:
            pass
        try:
            popup = menu.getPopupLayout()
            if popup is not None:
                ll = getattr(popup, "linearLayout", None)
                if ll is not None:
                    count = ll.getChildCount()
                    for i in range(count):
                        child = ll.getChildAt(i)
                        if child is None:
                            continue
                        if child.getId() == item_id:
                            return True
                        tag = child.getTag()
                        if tag is not None and str(tag) == str(item_id):
                            return True
        except BaseException:
            pass
        return False

    def _add_menu_items_if_needed(self, menu, layout, parent_alert):
        try:
            plugin_ref = self
            icon_res = self._get_icon_res(parent_alert)

            def on_click_action(send_first):
                try:
                    menu.closeSubMenu()
                except BaseException:
                    pass
                plugin_ref._on_action(layout, parent_alert, send_first=send_first)

            if not self._has_sub_item(menu, DELETE_ITEM_ID):
                sub_del = menu.addSubItem(DELETE_ITEM_ID, icon_res, L.g("delete_from_device"))
                if sub_del is not None:
                    try:
                        sub_del.setId(DELETE_ITEM_ID)
                        sub_del.setTag(DELETE_ITEM_ID)
                        sub_del.setOnClickListener(OnClickListener(lambda v: on_click_action(False)))
                    except BaseException:
                        pass

            if not self._has_sub_item(menu, SEND_AND_DELETE_ITEM_ID):
                sub_send = menu.addSubItem(SEND_AND_DELETE_ITEM_ID, icon_res, L.g("send_and_delete"))
                if sub_send is not None:
                    try:
                        sub_send.setId(SEND_AND_DELETE_ITEM_ID)
                        sub_send.setTag(SEND_AND_DELETE_ITEM_ID)
                        sub_send.setOnClickListener(OnClickListener(lambda v: on_click_action(True)))
                    except BaseException:
                        pass
        except BaseException as e:
            self.log(f"[DeleteFromGallery] Add menu items error: {e}")

    def _on_action(self, layout, parent_alert, send_first=False):
        now = time.time()
        if (now - getattr(self, "_last_action_time", 0.0)) < 0.8:
            return
        self._last_action_time = now

        try:
            self._perform_delete(layout, parent_alert, send_first=send_first)
        except BaseException as e:
            self.log(f"[DeleteFromGallery] Action error: {e}")

    def _get_icon_res(self, parent_alert):
        try:
            from org.telegram.messenger import R
            return R.drawable.msg_delete
        except BaseException:
            return 0

    def _get_activity(self, parent_alert):
        try:
            base_frag = getattr(parent_alert, "baseFragment", None)
            if base_frag is not None:
                act = base_frag.getParentActivity()
                if act is not None:
                    return act
        except BaseException:
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
                except BaseException:
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
                    except BaseException:
                        pass
        except BaseException as e:
            self.log(f"[DeleteFromGallery] Album cleanup error: {e}")

    def _send_media(self, parent_alert):
        try:
            photo_layout = getattr(parent_alert, "photoLayout", None)
            if photo_layout is not None:
                try:
                    photo_layout.sendSelectedPhotos(False)
                    return
                except BaseException:
                    pass
            parent_alert.sendPressed(True, 0)
        except BaseException:
            try:
                parent_alert.sendPressed(True, 0)
            except BaseException as e:
                self.log(f"[DeleteFromGallery] Send media error: {e}")

    def _clear_selection(self, layout, parent_alert):
        def do_clear():
            try:
                if layout is not None:
                    try:
                        layout.clearSelectedPhotos()
                    except BaseException:
                        pass
                if parent_alert is not None:
                    try:
                        parent_alert.updateCountButton(0)
                    except BaseException:
                        pass
            except BaseException as e:
                self.log(f"[DeleteFromGallery] Clear selection error: {e}")

        try:
            run_on_ui_thread(do_clear)
        except BaseException:
            pass

    def _execute_media_deletion(self, activity, resolver, uris, valid, sdk):
        try:
            if sdk >= 30:
                try:
                    from android.provider import MediaStore
                    pi = MediaStore.createDeleteRequest(resolver, uris)
                    if activity is not None:
                        activity.startIntentSenderForResult(pi.getIntentSender(), 110, None, 0, 0, 0)
                        self._safe_notify(L.g("confirm_delete"), is_error=False)
                    else:
                        self._safe_notify(L.g("cannot_get_activity"), is_error=True)
                except BaseException as e:
                    self.log(f"[DeleteFromGallery] createDeleteRequest error: {e}")
                    self._safe_notify(L.g("failed_request_delete"), is_error=True)
            else:
                deleted = 0
                for i in range(uris.size()):
                    try:
                        if resolver.delete(uris.get(i), None, None) > 0:
                            deleted += 1
                    except BaseException as e:
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
                        except BaseException:
                            pass

                if deleted > 0:
                    self._safe_notify(L.g("deleted_count", deleted), is_error=False)
                else:
                    self._safe_notify(L.g("cannot_delete_files"), is_error=True)

            self._clean_media_controller_albums(valid)
        except BaseException as e:
            self.log(f"[DeleteFromGallery] Media deletion error: {e}")

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
            except BaseException:
                pass

        sel_photos = getattr(ChatAttachAlertPhotoLayout, "selectedPhotos", None)
        if sel_photos is None or sel_photos.isEmpty():
            self._safe_notify(L.g("no_media_selected"), is_error=True)
            return

        entries = []
        try:
            it = sel_photos.values().iterator()
            while it.hasNext():
                entries.append(it.next())
        except BaseException as e:
            self.log(f"[DeleteFromGallery] Read selectedPhotos error: {e}")

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
                is_video = bool(getattr(entry, "isVideo", False))
                base = MediaStore.Video.Media.EXTERNAL_CONTENT_URI if is_video else MediaStore.Images.Media.EXTERNAL_CONTENT_URI
                uris.add(ContentUris.withAppendedId(base, img_id))
                valid.append(entry)
            except BaseException as e:
                self.log(f"[DeleteFromGallery] URI build error: {e}")

        if uris.isEmpty():
            self._safe_notify(L.g("no_valid_media"), is_error=True)
            return

        activity = self._get_activity(parent_alert)

        if send_first:
            self._send_media(parent_alert)

            def do_delayed_delete():
                try:
                    self._execute_media_deletion(activity, resolver, uris, valid, sdk)
                except BaseException as e:
                    self.log(f"[DeleteFromGallery] Delayed delete error: {e}")

            try:
                run_on_ui_thread(do_delayed_delete, 400)
            except BaseException:
                import threading
                threading.Timer(0.4, lambda: run_on_ui_thread(do_delayed_delete)).start()
        else:
            self._clear_selection(layout, parent_alert)
            self._execute_media_deletion(activity, resolver, uris, valid, sdk)


# __DEX_BEGIN__
# PLACEHOLDER
# __DEX_END__
