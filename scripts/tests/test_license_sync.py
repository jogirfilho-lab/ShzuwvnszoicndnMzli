"""Run the actual generated license store and countdown code on the macOS runner."""
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[2]
a = (root / 'App.swift').read_text()
response_start = a.index('struct LicenseResponse: Codable {')
response_end = a.index('\nenum LicenseAPI {', response_start)
store_start = a.index('final class LicenseStore {')
store_end = a.index('\nstruct LicenseProfileView: View {', store_start)
store = a[store_start:store_end]
# Use a disposable service/account on the ephemeral runner, never the app's own Keychain item.
store = store.replace('"com.threeoneosfive.license"', '"injectchz.unit-tests"')
store = store.replace('"activation-key"', '"' + str(uuid.uuid4()) + '"')
with tempfile.TemporaryDirectory(prefix='inject-key-tests-') as directory:
    main = Path(directory) / 'main.swift'
    main.write_text('import Foundation\nimport Security\nimport CryptoKit\n' +
                    a[response_start:response_end] + '\n' + store + '\n' +
                    (repo / 'scripts/templates/license_clock.swift').read_text() + '\n' +
                    (repo / 'scripts/tests/license_clock_tests.swift').read_text())
    subprocess.run(['xcrun', 'swift', '-swift-version', '5', str(main)], check=True, timeout=120)
assert 'guard LicenseStore.storedKey == key else { return }' in a
assert 'onReceive(NotificationCenter.default.publisher(for: LicenseStore.profileDidChange))' in a
assert 'TimelineView(.periodic(from: .now, by: 1))' in a
print('Production home lifecycle and stale-response guards verified.')
