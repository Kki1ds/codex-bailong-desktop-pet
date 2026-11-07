"""Mac desktop integration introduced by the cumulative 1.6.0 merge."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import mac_native
from roaming_window import ForegroundGeometry

@unittest.skipUnless(sys.platform=='darwin','macOS integration')
class Mac160Tests(unittest.TestCase):
    def test_negative_origin_and_retina_bounds_are_logical_points(self):
        self.assertEqual(mac_native.clipped_geometry((-2500,20,-500,900),(-1920,0,1920,1080)),(-1920,20,-500,900))
        self.assertIsNone(mac_native.clipped_geometry((0,0,900,900),(-1920,0,1920,1080)))
    def test_roaming_passes_monitor_bounds_without_dividing_by_dpr(self):
        pet=Mock();g=pet.screen.return_value.geometry.return_value
        g.x.return_value=-1920;g.y.return_value=200;g.width.return_value=1920;g.height.return_value=1080
        with patch('mac_native.foreground_geometry',return_value=(-1800,250,-900,800)) as read:
            self.assertEqual(ForegroundGeometry().read(pet),(-1800,250,-900,800))
        read.assert_called_once_with((-1920,200,1920,1080),os.getpid())
    def test_roaming_handles_unavailable_geometry(self):
        pet=Mock();pet.screen.return_value=None
        self.assertIsNone(ForegroundGeometry().read(pet))
        pet.screen.return_value=Mock()
        with patch('mac_native.foreground_geometry',side_effect=OSError('unavailable')):
            self.assertIsNone(ForegroundGeometry().read(pet))
    def test_frontmost_own_app_never_queries_other_windows(self):
        with patch('mac_native._runtime') as runtime,patch('mac_native._send',side_effect=[1,2,os.getpid()]),patch('mac_native._quartz') as quartz:
            self.assertIsNone(mac_native.foreground_geometry((0,0,100,100),os.getpid()))
        quartz.assert_not_called()
    def test_pricing_files_use_existing_data_root(self):
        import cost_preferences,official_api_prices
        with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,LOCALAPPDATA=root):
            self.assertEqual(cost_preferences.path(),Path(root)/'BailongEnhanced/cost-pricing.json')
            self.assertEqual(official_api_prices.cache_path(),Path(root)/'BailongEnhanced/official-api-prices.json')
    def test_pricing_default_uses_application_support(self):
        import cost_preferences,official_api_prices
        with patch.dict(os.environ,{},clear=True):
            expected=Path.home()/'Library/Application Support/BailongEnhanced'
            self.assertEqual(cost_preferences.path().parent,expected)
            self.assertEqual(official_api_prices.cache_path().parent,expected)

    def test_database_maintenance_keeps_user_symlink_protection(self):
        from index_maintenance import plain
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'real';target.mkdir();link=root/'linked';link.symlink_to(target)
            self.assertEqual(plain(root/'tokens.sqlite3'),root.resolve()/'tokens.sqlite3')
            with self.assertRaises(ValueError):plain(link/'tokens.sqlite3')
