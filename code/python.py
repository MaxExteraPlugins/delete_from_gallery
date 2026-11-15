__id__ = "delete_from_gallery"
__name__ = "Delete From Gallery"
__description__ = (
    "Adds 'Delete from device' and 'Send and delete' buttons to the attachment picker menu.\n\n"
    "Добавляет кнопки «Удалить с устройства» и «Отправить и удалить» в меню выбора медиа."
)
__author__ = "@itNotMax - @MaxExteraPlugins"
__version__ = "1.1"
__icon__ = "MaxExteraPluginsStickers/23"
__min_version__ = "12.10.6"
__app_version__ = ">=12.10.6"
__sdk_version__ = ">=1.4.3.3"

from base_plugin import BasePlugin, MethodHook
from android_utils import run_on_ui_thread, OnClickListener
from hook_utils import get_private_field


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
            self._setup_hook()
        except Exception as e:
            self.log(f"[DeleteFromGallery] Hook setup error: {e}")

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
                                    try:
                                        tag = ll.getChildAt(i).getTag()
                                        if tag is not None:
                                            existing_ids.add(int(tag))
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                    from org.telegram.messenger import R as R_tg

                    if SEND_AND_DELETE_ITEM_ID not in existing_ids:
                        sub_send = menu.addSubItem(
                            SEND_AND_DELETE_ITEM_ID,
                            R_tg.drawable.msg_send,
                            L.g("send_and_delete"),
                        )
                        sub_send.setOnClickListener(OnClickListener(
                            lambda v, lo=layout, p=pa: plugin_ref._on_send_and_delete(lo, p)
                        ))

                    if DELETE_ITEM_ID not in existing_ids:
                        sub_del = menu.addSubItem(
                            DELETE_ITEM_ID,
                            R_tg.drawable.msg_delete,
                            L.g("delete_from_device"),
                        )
                        sub_del.setOnClickListener(OnClickListener(
                            lambda v, lo=layout, p=pa: plugin_ref._on_delete(lo, p)
                        ))
                except Exception as e:
                    plugin_ref.log(f"[DeleteFromGallery] Menu hook error: {e}")

        self.hook_method(method, MenuHook())

    def _on_delete(self, layout, parent_alert):
        try:
            self._perform_delete(layout, parent_alert, send_first=False)
        except Exception as e:
            self.log(f"[DeleteFromGallery] Delete error: {e}")

    def _on_send_and_delete(self, layout, parent_alert):
        try:
            self._perform_delete(layout, parent_alert, send_first=True)
        except Exception as e:
            self.log(f"[DeleteFromGallery] Send and delete error: {e}")

    def _get_activity(self, parent_alert):
        activity = None
        try:
            bf = getattr(parent_alert, "baseFragment", None)
            if bf is not None:
                activity = bf.getParentActivity()
        except Exception:
            pass
        if activity is None:
            try:
                activity = parent_alert.getOwnerActivity()
            except Exception:
                pass
        if activity is None:
            try:
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if frag is not None:
                    activity = frag.getParentActivity()
            except Exception:
                pass
        return activity

    def _send_media(self, parent_alert):
        write_btn = None
        try:
            write_btn = get_private_field(parent_alert, "writeButton")
        except Exception:
            pass

        sent = False
        if write_btn is not None:
            try:
                write_btn.performClick()
                sent = True
            except Exception as e:
                self.log(f"[DeleteFromGallery] writeButton performClick error: {e}")

        if not sent:
            try:
                done_item = getattr(parent_alert, "doneItem", None)
                if done_item is not None:
                    done_item.performClick()
                    sent = True
            except Exception as e:
                self.log(f"[DeleteFromGallery] doneItem performClick error: {e}")

        if not sent:
            try:
                method = parent_alert.getClass().getDeclaredMethod("onWriteButtonPressed")
                method.setAccessible(True)
                method.invoke(parent_alert)
                sent = True
            except Exception as e:
                self.log(f"[DeleteFromGallery] onWriteButtonPressed invocation error: {e}")

        return sent

    def _clean_media_controller_albums(self, entries):
        try:
            from org.telegram.messenger import MediaController
            for album_entry in [
                getattr(MediaController, "allMediaAlbumEntry", None),
                getattr(MediaController, "allPhotosAlbumEntry", None),
                getattr(MediaController, "allVideosAlbumEntry", None),
            ]:
                if album_entry is not None and getattr(album_entry, "photos", None) is not None:
                    for e in entries:
                        try:
                            album_entry.photos.remove(e)
                        except Exception:
                            pass
        except Exception as e:
            self.log(f"[DeleteFromGallery] Clean MediaController error: {e}")

    def _clear_selection(self, layout, parent_alert, entries):
        from org.telegram.ui.Components import ChatAttachAlertPhotoLayout

        def do_clear():
            try:
                try:
                    if ChatAttachAlertPhotoLayout.selectedPhotos is not None:
                        ChatAttachAlertPhotoLayout.selectedPhotos.clear()
                    if ChatAttachAlertPhotoLayout.selectedPhotosOrder is not None:
                        ChatAttachAlertPhotoLayout.selectedPhotosOrder.clear()
                except Exception:
                    pass

                try:
                    album = getattr(layout, "selectedAlbumEntry", None)
                    if album is None:
                        album = get_private_field(layout, "selectedAlbumEntry")
                    if album is not None and getattr(album, "photos", None) is not None:
                        for e in entries:
                            try:
                                album.photos.remove(e)
                            except Exception:
                                pass
                except Exception:
                    pass

                self._clean_media_controller_albums(entries)

                try:
                    adapter = getattr(layout, "adapter", None)
                    if adapter is None:
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
        from ui.bulletin import BulletinHelper

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
        from ui.bulletin import BulletinHelper

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
