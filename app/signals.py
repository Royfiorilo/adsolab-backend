from blinker import Namespace

_signals = Namespace()

version_saved = _signals.signal('version-saved')
version_deleted = _signals.signal('version-deleted')