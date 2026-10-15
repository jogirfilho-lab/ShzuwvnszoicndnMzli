"""Integrate reference home and lowercase brand after all legacy transforms."""
from pathlib import Path
import json
import plistlib
import re
import shutil
import sys

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parent.parent
app = root / 'App.swift'
a = app.read_text()
assert 'struct InjectLicenseHomeView: View' not in a, 'Reference transform already applied'
login_start = a.index('struct LicenseLoginView: View')
logic_start = a.index('    private func validateStoredKey()', login_start)
logic_end = a.index('\n}\n', logic_start)
original_login_logic = a[logic_start:logic_end]
header_start = a.index('                        Text("EXTERNAL CHZ")', login_start)
header_end = a.index('                        VStack(alignment: .leading, spacing: 9)', header_start)
logo = '''                        Image("InjectCHZLogo")
                            .resizable()
                            .scaledToFit()
                            .frame(width: 240, height: 100)
                            .accessibilityLabel("inject chz")
                            .padding(.top, 16)
'''
a = a[:header_start] + logo + a[header_end:]
a = a.replace('product: "EXTERNAL",', 'product: "inject chz",', 1)
a += (repo / 'scripts/templates/inject_license_home.swift').read_text()
assert original_login_logic in a, 'Authentication logic must remain unchanged'
app.write_text(a)

assets = root / 'Assets.xcassets/InjectCHZLogo.imageset'
assets.mkdir(parents=True, exist_ok=True)
shutil.copy2(repo / 'resources/inject-chz-brand.png', assets / 'inject-chz-brand.png')
(assets / 'Contents.json').write_text(json.dumps({
    'images': [{'filename': 'inject-chz-brand.png', 'idiom': 'universal'}],
    'info': {'author': 'xcode', 'version': 1}
}, indent=2) + '\n')

content = root / 'ContentView.swift'
c = content.read_text()
c, count = re.subn(r'case \.home:\s*NavigationStack \{\s*Form \{ LicenseProfileView\(\) \}\s*\.scrollContentBackground\(\.hidden\)\s*\.background\(Color.black\)\s*\.navigationTitle\("Licença"\)\s*\.preferredColorScheme\(\.dark\)\s*\}', 'case .home:\n            InjectLicenseHomeView()', c, count=1)
assert count == 1, 'Actual home section missing'
start = c.index('    private var compactLayout: some View {')
end = c.index('    private var regularLayout: some View {', start)
compact = '''    private var compactLayout: some View {
        sectionContent(selectedVisibleSection)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .safeAreaInset(edge: .bottom, spacing: 0) {
                HStack(spacing: 5) {
                    ForEach([AppSection.home, .patches, .external, .textures]) { section in
                        let selected = tabNavigation.selectedTab == section.rawValue
                        Button {
                            withAnimation(.easeInOut(duration: 0.16)) { tabNavigation.select(section.rawValue) }
                        } label: {
                            VStack(spacing: 5) {
                                Image(systemName: injectIcon(section)).font(.system(size: 18, weight: .semibold))
                                Text(injectTitle(section)).font(.system(size: 9, weight: .semibold))
                            }
                            .foregroundStyle(selected ? Color(red: 0.96, green: 0.12, blue: 0.20) : Color.white.opacity(0.46))
                            .frame(maxWidth: .infinity).frame(height: 48)
                            .background(selected ? Color.red.opacity(0.10) : Color.clear, in: RoundedRectangle(cornerRadius: 14))
                            .overlay(RoundedRectangle(cornerRadius: 14).stroke(selected ? Color.red.opacity(0.30) : Color.clear, lineWidth: 0.5))
                        }.buttonStyle(.plain).accessibilityAddTraits(selected ? .isSelected : [])
                    }
                }
                .padding(6)
                .background(Color(red: 0.055, green: 0.035, blue: 0.04), in: RoundedRectangle(cornerRadius: 19))
                .overlay(RoundedRectangle(cornerRadius: 19).stroke(Color(red: 0.58, green: 0.035, blue: 0.09), lineWidth: 1))
                .shadow(color: Color.red.opacity(0.10), radius: 8)
                .padding(.horizontal, 16).padding(.top, 6).padding(.bottom, 6)
                .background(Color.black)
            }
    }

    private func injectTitle(_ section: AppSection) -> String {
        switch section {
        case .home: return "Início"
        case .patches: return "Injetor"
        case .external: return "External"
        case .textures: return "Texturas"
        default: return ""
        }
    }
    private func injectIcon(_ section: AppSection) -> String {
        switch section {
        case .home: return "house.fill"
        case .patches: return "syringe"
        case .external: return "square.3.layers.3d.fill"
        case .textures: return "paintpalette.fill"
        default: return "circle"
        }
    }

'''
c = c[:start] + compact + c[end:]
c = c.replace('?? .patches', '?? .home')
c = c.replace('initialTab = AppSection.patches.rawValue', 'initialTab = AppSection.home.rawValue')
content.write_text(c)
nav = root / 'helpers/AppTabNavigationState.swift'
n = nav.read_text().replace('selectedTab: Int = AppSection.patches.rawValue', 'selectedTab: Int = AppSection.home.rawValue')
nav.write_text(n)
for marker in ['InjectLicenseHomeView()', 'safeAreaInset(edge: .bottom', '.textures']:
    assert marker in content.read_text(), marker
assert 'RENOVAR OU GERENCIAR' not in (repo / 'scripts/templates/inject_license_home.swift').read_text()
assert 'LicenseAPI.validate(key: candidate)' in app.read_text()
# Rename visible/product metadata only; preserve bundle identifier and API contract.
info = root / 'Info.plist'
with info.open('rb') as handle:
    values = plistlib.load(handle)
original_bundle_id = values.get('CFBundleIdentifier')
values['CFBundleDisplayName'] = 'inject chz'
values['CFBundleName'] = 'injectchz'
assert values.get('CFBundleIdentifier') == original_bundle_id
with info.open('wb') as handle:
    plistlib.dump(values, handle, sort_keys=False)
project = root.parent / 'ThreeOneOSFive.xcodeproj/project.pbxproj'
p = project.read_text()
p = re.sub(r'INFOPLIST_KEY_CFBundleDisplayName = [^;]+;', 'INFOPLIST_KEY_CFBundleDisplayName = "inject chz";', p)
p = re.sub(r'INFOPLIST_KEY_CFBundleName = [^;]+;', 'INFOPLIST_KEY_CFBundleName = injectchz;', p)
p, count = re.subn(r'PRODUCT_NAME = (?:EXTERNALCHZ|3105);', 'PRODUCT_NAME = injectchz;', p)
assert count > 0, 'Expected product name not found'
project.write_text(p)
print('inject chz home and key branding applied; existing auth/actions preserved.')
