"""Apply branding and a local-only shell to fresh ORIGINAL sources; never inject backend code."""
from pathlib import Path
import json, plistlib, re, shutil, sys
root = Path(sys.argv[1])
repo = Path(__file__).resolve().parent.parent

p = root / 'App.swift'
s = p.read_text()
a = s.index('    private func checkForUpdate() {')
b = s.index('\n    var body: some Scene {', a)
s = s[:a] + '    private func checkForUpdate() {}\n' + s[b:]
s = s.replace('@State private var showOnboarding = OnboardingStore.shouldShow()', '@State private var showOnboarding = false')
p.write_text(s)

p = root / 'helpers/Utils.swift'
s = p.read_text()
s = re.sub(r'^    static let (apiURL|fallbackURL) = .*\n', '', s, flags=re.M)
a = s.index('    static func check() async -> Offer? {')
b = s.index('\n    private struct GitHubRelease:', a)
s = s[:a] + '    static func check() async -> Offer? { nil }\n' + s[b:]
p.write_text(s)

p = root / 'helpers/PackageRepositoryStore.swift'
s = p.read_text()
a = s.index('private final class PackageRepositoryRedirectDelegate:')
s = s[:a] + '''enum PackageRepositoryNetworkClient {
    static func loadSourceCatalog(from catalogURL: URL) async throws -> [URL] { [] }
    static func loadRepository(from sourceURL: URL) async throws -> PackageRepository { throw URLError(.notConnectedToInternet) }
    static func download(_ package: RepositoryPackage) async throws -> Data { throw URLError(.notConnectedToInternet) }
    static func downloadWallpaper(_ package: RepositoryPackage) async throws -> URL { throw URLError(.notConnectedToInternet) }
}
'''
p.write_text(s)

shutil.copyfile(repo / 'scripts/offline/ContentView.swift', root / 'ContentView.swift')
p = root / 'views/DesignSystem.swift'
s = p.read_text()
a = s.index('    static let accent = Color(')
b = s.index('    static let pageBackground', a)
s = s[:a] + '    static let accent = Color(red: 0.96, green: 0.12, blue: 0.20)\n' + s[b:]
p.write_text(s)

images = root / 'Assets.xcassets/InjectCHZLogo.imageset'
images.mkdir(parents=True, exist_ok=True)
shutil.copyfile(repo / 'resources/inject-chz-brand.png', images / 'inject-chz.png')
(images / 'Contents.json').write_text(json.dumps({'images': [{'idiom': 'universal', 'filename': 'inject-chz.png'}], 'info': {'author': 'xcode', 'version': 1}}, indent=2) + '\n')
p = root / 'Info.plist'
info = plistlib.loads(p.read_bytes())
info['CFBundleDisplayName'] = 'inject chz'
info['CFBundleName'] = 'injectchz'
p.write_bytes(plistlib.dumps(info))
p = root.parent / 'ThreeOneOSFive.xcodeproj/project.pbxproj'
s = p.read_text()
s = re.sub(r'PRODUCT_NAME = [^;]+;', 'PRODUCT_NAME = injectchz;', s)
s = re.sub(r'INFOPLIST_KEY_CFBundleDisplayName = [^;]+;', 'INFOPLIST_KEY_CFBundleDisplayName = "inject chz";', s)
p.write_text(s)

all_code = '\n'.join(p.read_text() for p in root.rglob('*.swift'))
for forbidden in ['knzgen.up.railway.app', 'X-PH-IOS-Token', 'LicenseAPI', 'LicenseStore', 'RemotePatchAPI', 'ExternalPanelView', 'struct LicenseLoginView']:
    assert forbidden not in all_code, 'Remote integration remains: ' + forbidden
assert 'PatchProjectsView(onOpenSettings:' in (root / 'ContentView.swift').read_text()
assert 'store.importPackage(at: url)' in (root / 'views/PatchProjectsView.swift').read_text()
assert 'Task' not in (root / 'helpers/Utils.swift').read_text().split('static func check() async -> Offer?')[1].split('private struct GitHubRelease')[0]
print('Local variant verified: no key gate or backend clients; native .3105 importer preserved.')
