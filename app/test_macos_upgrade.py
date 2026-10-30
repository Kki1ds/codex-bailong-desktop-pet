"""macOS 1.2.1 compatibility and general full-screen policy regressions."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent
from desktop import DesktopPet
from desktop_core import normalized
import mac_native as native

APP=QApplication.instance() or QApplication([])

@unittest.skipUnless(sys.platform=='darwin','macOS upgrade')
class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.patches=[patch('enhanced.STATE_DIR',self.root),patch('enhanced.CONFIG',self.root/'settings.json'),
            patch('desktop.STATE_DIR',self.root),patch('desktop.CONFIG',self.root/'settings.json')]
        for p in self.patches:p.start()
        self.pet=DesktopPet(monitor=False);self.pet.apply_settings(dict(character_visible=False,random_actions=False,wandering=False),save=False)
        self.pet.bubble.size_transition.complete();APP.processEvents()
        self.guard=native.FullScreenGuard(self.pet)
    def tearDown(self):
        self.guard.timer.stop();native._guard=None;native._yield=True
        self.pet.close();APP.processEvents();APP.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def test_old_and_new_modes_migrate_to_general_policy(self):
        for raw in ({},{'video_fullscreen_yield':True},{'fullscreen_yield_mode':'video'},{'fullscreen_yield_mode':'all'}):
            self.assertEqual(normalized(raw)['fullscreen_yield_mode'],'game_video')
        for raw in ({'video_fullscreen_yield':False},{'fullscreen_yield_mode':'off'}):
            self.assertEqual(normalized(raw)['fullscreen_yield_mode'],'off')
    def test_hidden_geometry_keeps_yielding_until_fullscreen_exits(self):
        g=self.pet.bubble.frameGeometry();display=(g.x()-5,g.y()-5,g.width()+10,g.height()+10)
        with patch.object(native,'full_screen_displays',return_value=[display]):
            self.guard.check();self.assertTrue(self.pet._fullscreen_yielded);self.assertFalse(self.pet.bubble.isVisible())
            self.guard.check();self.assertTrue(self.pet._fullscreen_yielded)
            self.pet.bubble.status_indicator.unread={'pending-turn'};self.pet.sync_full_screen()
            self.guard.check();self.assertTrue(self.pet._fullscreen_yielded);self.assertFalse(self.pet.bubble.isVisible())
        with patch.object(native,'full_screen_displays',return_value=[]):
            self.guard.check();self.assertFalse(self.pet._fullscreen_yielded);self.assertTrue(self.pet.bubble.isVisible())
    def test_yield_disabled_restores_without_reenabling_topmost(self):
        self.pet.apply_settings(dict(on_top=False),save=False)
        g=self.pet.bubble.frameGeometry()
        with patch.object(native,'full_screen_displays',return_value=[(g.x(),g.y(),g.width(),g.height())]):
            self.guard.check();self.assertTrue(self.pet._fullscreen_yielded)
            self.pet.apply_settings(dict(fullscreen_yield_mode='off'),save=False)
            self.assertFalse(self.pet._fullscreen_yielded);self.assertFalse(self.pet.settings['on_top'])
    def test_settings_expose_general_mode_and_no_windows_installer(self):
        self.pet.open_settings();s=self.pet.settings_dialog
        s.build_page(0);self.assertEqual([key for label,key in s.fullscreen_mode.items],['off','game_video'])
        s.build_page(5)
        from PySide6.QtWidgets import QPushButton
        self.assertNotIn('程序位置与安装管理',[b.text() for b in s.findChildren(QPushButton)])
    def test_native_menu_bar_tooltip_and_no_hover_polling(self):
        self.pet.quota_windows=[dict(name='5小时',remaining=64,resetsAt=None)]
        self.pet._refresh_tray_icon()
        self.assertIn('64%',self.pet.tray.toolTip());self.assertFalse(self.pet.tray_hover.watch.isActive())
    def test_material_paths_accept_system_alias_but_reject_user_symlinks(self):
        from storage_locations import plain,data_dir
        self.assertEqual(plain(self.root),self.root.resolve())
        link=self.root/'linked';target=self.root/'real';target.mkdir();link.symlink_to(target)
        with self.assertRaises(ValueError):plain(link/'child')
        with patch.dict(os.environ,LOCALAPPDATA=str(self.root)):
            self.assertEqual(data_dir(),self.root/'BailongEnhanced')
