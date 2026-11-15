# -*- coding: utf-8 -*-
__id__ = "delete_from_gallery"
__name__ = "Delete From Gallery"
__description__ = (
    "Adds 'Delete from device' and 'Send and delete' buttons to the attachment picker menu.\n\n"
    "Добавляет кнопки «Удалить с устройства» и «Отправить и удалить» в меню выбора медиа."
)
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.1.0"
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
    "trial_days": 7
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
            "ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работать без ограничений",
            "en": "Thank you for subscribing to our channel!\nThe plugin will continue working without restrictions",
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


class DeleteFromGalleryPlugin(BasePlugin):

    def on_plugin_load(self):
        try:
            self._load_remote_links_async()
            self._check_initial_subscription_flow()
            self._setup_hook()
        except Exception as e:
            self.log(f"[DeleteFromGallery] Hook setup error: {e}")

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
    def create_settings(self) -> List[Any]:
        links = self._get_links()
        channel_url = links.get("channel_url", "https://t.me/MaxExteraPlugins")
        donate_url = links.get("donate_url", "https://t.me/itNotMax")
        username = links.get("channel_username", "MaxExteraPlugins")

        def open_channel(v=None):
            self._open_url(channel_url, v)

        def open_donate(v=None):
            self._open_url(donate_url, v)

        items = [
            Header(text="MaxExteraPlugins"),
            Text(
                text=L.g("settings_channel"),
                subtext=f"@{username}",
                icon="msg_channel",
                on_click=open_channel,
            ),
            Text(
                text=L.g("settings_donate"),
                subtext=L.g("settings_donate_sub"),
                icon="msg_share",
                on_click=open_donate,
            ),
            Divider(),
        ]
        return items

    # ============================================================
    # Top Card Icon View (Plugin Sticker / Icon)
    # ============================================================
    def _create_card_icon_view(self, act):
        try:
            from android.widget import FrameLayout, ImageView, TextView
            from android.view import Gravity
            from android.graphics.drawable import GradientDrawable
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController, ImageLocation, R
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp
            container = FrameLayout(act)
            container.setPadding(0, dp(20), 0, dp(4))

            size = dp(68)
            box = FrameLayout(act)

            bg = GradientDrawable()
            accent = Theme.getColor(Theme.key_featuredStickers_addButton)
            bg.setColor(accent)
            bg.setCornerRadius(float(dp(20)))
            box.setBackground(bg)

            loaded = False
            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                pack = "MaxExteraPluginsStickers"
                sticker_set = mdc.getStickerSetByName(pack)
                if sticker_set is not None and sticker_set.documents is not None and sticker_set.documents.size() > 23:
                    doc = sticker_set.documents.get(23)
                    iv = BackupImageView(act)
                    iv.setRoundRadius(dp(20))
                    iv.setImage(ImageLocation.getForDocument(doc), "68_68", None, None, sticker_set)
                    box.addView(iv, FrameLayout.LayoutParams(size, size, Gravity.CENTER))
                    loaded = True
                else:
                    mdc.loadStickersByEmojiOrName(pack, False, True)
            except Exception:
                pass

            if not loaded:
                try:
                    iv = ImageView(act)
                    iv.setImageResource(R.drawable.msg_delete)
                    iv.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhite))
                    pad = dp(16)
                    iv.setPadding(pad, pad, pad, pad)
                    box.addView(iv, FrameLayout.LayoutParams(size, size, Gravity.CENTER))
                except Exception:
                    tv = TextView(act)
                    tv.setText("🗑️")
                    tv.setTextSize(26.0)
                    tv.setGravity(Gravity.CENTER)
                    box.addView(tv, FrameLayout.LayoutParams(size, size, Gravity.CENTER))

            lp = FrameLayout.LayoutParams(size, size, Gravity.CENTER_HORIZONTAL)
            container.addView(box, lp)
            return container
        except Exception as e:
            self.log(f"[DeleteFromGallery] Create card icon error: {e}")
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

            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)

            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed_to_channel(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = links.get("channel_username", "MaxExteraPlugins").lower().lstrip("@")

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated():
                    continue

                mc = MessagesController.getInstance(acc)
                if not mc:
                    continue

                chat = mc.getUserOrChat(target)
                if chat is not None:
                    left = getattr(chat, "left", True)
                    kicked = getattr(chat, "kicked", False)
                    if not left and not kicked:
                        return True

                dialogs = mc.allDialogs
                if dialogs is not None:
                    limit = min(dialogs.size(), 250)
                    for i in range(limit):
                        d = dialogs.get(i)
                        did = getattr(d, "id", 0)
                        if did < 0:
                            from java.lang import Long as JLong
                            c = mc.getChat(JLong(-did))
                            if c is not None:
                                uname = str(getattr(c, "username", "") or "").lower()
                                if uname == target:
                                    if not getattr(c, "left", True) and not getattr(c, "kicked", False):
                                        return True
        except Exception as e:
            self.log(f"[DeleteFromGallery] is_subscribed error: {e}")
        return False

    def _notify_subscribed(self, was_expired=False):
        self.set_setting("was_subscribed", True)
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(L.g(msg_key))

    def _check_initial_subscription_flow(self):
        def flow():
            try:
                now = time.time()
                install_time = float(self.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.set_setting("install_time", install_time)

                is_sub = self.is_subscribed_to_channel()
                was_sub = bool(self.get_setting("was_subscribed", False))

                if is_sub:
                    if not was_sub:
                        self._notify_subscribed(was_expired=False)
                    return

                # User is NOT subscribed
                if was_sub:
                    self.set_setting("was_subscribed", False)
                    self.set_setting("last_remind_time", 0.0)

                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self._show_expired_card()

            except Exception as e:
                self.log(f"[DeleteFromGallery] Initial flow error: {e}")

        run_on_ui_thread(flow, 1500)

    def is_feature_allowed(self) -> bool:
        if self.is_subscribed_to_channel():
            if not self.get_setting("was_subscribed", False):
                was_expired = bool(self.get_setting("was_expired_state", False))
                self.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_expired)
            return True

        now = time.time()
        install_time = float(self.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        # Trial expired - record expired state and block
        self.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def _show_welcome_card(self):
        def show():
            try:
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                b = AlertDialogBuilder(act)
                top_view = self._create_card_icon_view(act)
                raw_b = getattr(b, "builder", None) or getattr(b, "_builder", None)
                if raw_b is not None and top_view is not None:
                    try:
                        raw_b.setTopView(top_view)
                        raw_b.notDrawBackgroundOnTopView(True)
                    except Exception:
                        pass

                b.set_title(L.g("install_card_title"))
                b.set_message(L.g("install_card_msg"))

                def on_sub(d, w):
                    try:
                        d.dismiss()
                    except Exception:
                        pass
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed_to_channel():
                            self._notify_subscribed(was_expired=False)
                    run_on_ui_thread(check_after, 3500)

                def on_later(d, w):
                    try:
                        d.dismiss()
                    except Exception:
                        pass
                    self.set_setting("last_remind_time", time.time())

                b.set_positive_button(L.g("subscribe_btn"), on_sub)
                b.set_negative_button(L.g("remind_later_btn"), on_later)
                b.show()
            except Exception as e:
                self.log(f"[DeleteFromGallery] Welcome card error: {e}")

        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                b = AlertDialogBuilder(act)
                top_view = self._create_card_icon_view(act)
                raw_b = getattr(b, "builder", None) or getattr(b, "_builder", None)
                if raw_b is not None and top_view is not None:
                    try:
                        raw_b.setTopView(top_view)
                        raw_b.notDrawBackgroundOnTopView(True)
                    except Exception:
                        pass

                b.set_title(L.g("trial_expired_title"))
                b.set_message(L.g("trial_expired_msg"))

                def on_sub(d, w):
                    try:
                        d.dismiss()
                    except Exception:
                        pass
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed_to_channel():
                            self._notify_subscribed(was_expired=True)
                    run_on_ui_thread(check_after, 3500)

                def on_check(d, w):
                    try:
                        d.dismiss()
                    except Exception:
                        pass
                    if self.is_subscribed_to_channel():
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(L.g("sub_not_found"))
                        self._show_expired_card()

                b.set_positive_button(L.g("subscribe_btn"), on_sub)
                b.set_negative_button(L.g("check_sub_btn"), on_check)
                b.show()
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
