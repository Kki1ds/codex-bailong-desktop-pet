"""Per-platform user folders.

Windows and Linux keep the original LOCALAPPDATA expression unchanged. Only
macOS, where LOCALAPPDATA is normally unset, falls back to Application Support.
"""
import os,sys
from pathlib import Path

WINDOWS=sys.platform=='win32'
MACOS=sys.platform=='darwin'
APP_ID='BailongEnhanced'
BUNDLE_ID='io.github.wunsch2048.bailong-enhanced'
# Hide console windows of helper processes; other systems take no flag.
NO_WINDOW=0x08000000 if WINDOWS else 0

def local_appdata(fallback=None):
    """Parent of the data folder; fallback replaces the home-directory default outside macOS."""
    if MACOS:
        # An explicit LOCALAPPDATA still isolates tests and QA runs on macOS.
        value=os.environ.get('LOCALAPPDATA')
        return Path(value) if value else Path.home()/'Library/Application Support'
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home() if fallback is None else fallback)))

def data_dir(fallback=None):return local_appdata(fallback)/APP_ID

def install_root():
    if WINDOWS:
        from storage_locations import install_root as registered_root
        return registered_root()
    return local_appdata()/'Programs'/APP_ID

def startup_folder():
    """Windows per-user Startup folder; macOS uses a LaunchAgent instead."""
    return Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup'

def launch_agents():
    # LOCALAPPDATA is only set on macOS to isolate tests/QA; keep their agents out of the real login.
    value=os.environ.get('LOCALAPPDATA')
    return Path(value)/'LaunchAgents' if value and MACOS else Path.home()/'Library/LaunchAgents'

def launch_agent(name=''):
    """(plist path, label) of a per-user LaunchAgent; name '' is the pet itself."""
    label=BUNDLE_ID+('.'+name if name else '');return launch_agents()/(label+'.plist'),label

def write_launch_agent(path,label,args,**extra):
    """Start at the next login only; nothing is loaded into launchd now."""
    import plistlib
    args=[str(a) for a in args]
    if '/AppTranslocation/' in args[0]:raise OSError('请先把白龙桌宠移到“应用程序”文件夹，再开启登录启动')
    # Children (watcher <-> pet) must survive this job exiting, as they do on Windows.
    data=plistlib.dumps(dict(Label=label,ProgramArguments=args,RunAtLoad=True,KeepAlive=False,AbandonProcessGroup=True,
        LimitLoadToSessionType='Aqua',WorkingDirectory=str(app_root()),**extra))
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_bytes(data);os.chmod(temp,0o644);os.replace(temp,path)

def launch_agent_args(path):
    """ProgramArguments of a run-at-login agent, or None when missing or unreadable."""
    import plistlib,xml.parsers.expat
    try:
        with open(path,'rb') as f:value=plistlib.load(f)
    except (OSError,ValueError,xml.parsers.expat.ExpatError):return None
    return value.get('ProgramArguments') if isinstance(value,dict) and value.get('RunAtLoad') is True else None

def background_python():
    """Interpreter for detached helpers: pythonw on Windows, the current one elsewhere."""
    return Path(sys.executable).with_name('pythonw.exe') if WINDOWS else Path(sys.executable)

def app_root():
    """Folder holding app/ and outputs/: the source tree, the Windows install folder, or a macOS bundle's Resources."""
    if getattr(sys,'frozen',False):
        exe=Path(sys.executable).resolve()
        return exe.parents[1]/'Resources' if MACOS and exe.parent.name=='MacOS' else exe.parent
    return Path(__file__).resolve().parents[1]
