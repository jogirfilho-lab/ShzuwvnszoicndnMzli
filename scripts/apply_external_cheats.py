"""Monochrome public branding only. Keep authenticated API and patch operations intact."""
from pathlib import Path
import json, plistlib, re, shutil, sys
root = Path(sys.argv[1])
repo = Path(__file__).resolve().parent.parent
brand = 'EXTERNAL CHEATS'

app_path = root / 'App.swift'
app_before = app_path.read_text()
login_start = app_before.index('    private func validateStoredKey()', app_before.index('struct LicenseLoginView: View'))
login_end = app_before.index('\n}\n', login_start)
login_logic = app_before[login_start:login_end]
patch_before = (root/'views/PatchProjectsView.swift').read_text()
protected_lines = [line.strip() for line in (app_before + '\n' + patch_before).splitlines()
                   if any(marker in line for marker in ['request.setValue(', 'request.httpBody =', 'URLSession.shared.data(', 'DevicePatchService.apply(', 'DevicePatchService.restore(', 'LicenseAPI.validate('])]

named_colors = 'red|green|blue|orange|yellow|pink|purple|cyan|mint|indigo|brown|teal'
rgb = re.compile(r'(Color|UIColor)\(\s*red:\s*([0-9.]+),\s*green:\s*([0-9.]+),\s*blue:\s*([0-9.]+)(?:,\s*alpha:\s*([0-9.]+))?\s*\)')
def grayscale_color(match):
    kind, r, g, b, alpha = match.groups()
    channels = list(map(float, [r,g,b]))
    if max(channels)-min(channels) < 0.045:
        level = sum(channels)/3
    elif max(channels) < 0.24:
        level = max(0.035, sum(channels)/3)
    elif max(channels) < 0.75:
        level = 0.32
    else:
        level = 1.0
    if kind == 'UIColor':
        return f'UIColor(white: {level:.3f}, alpha: {alpha or "1.0"})'
    return f'Color(white: {level:.3f})'

def update_literal(match):
    value=match.group(0)
    # Exact UI wordmarks; do not rename types, API headers, stored-key identifiers or bundle ID.
    for old in ['CHZ Project','Project CHZ','Projeto CHZ','PROJETO CHZ','CHZ PROJECT',
                'EXTERNAL CHZ','CHZ CHEATS','CHZ PRIV','inject chz','INJECT CHZ']:
        value=value.replace(old,brand)
    if value == '"CHZ"': value='"EXTERNAL"'
    value=value.replace('BLACK / RED EDITION','BLACK / WHITE EDITION')
    return value

for path in root.rglob('*.swift'):
    s=path.read_text()
    s=re.sub(r'"(?:[^"\\]|\\.)*"', update_literal, s)
    s=rgb.sub(grayscale_color,s)
    s=re.sub(r'Color\.('+named_colors+r')\b','Color.white',s)
    s=re.sub(r'UIColor\.('+named_colors+r')\b','UIColor.white',s)
    s=re.sub(r'(\.(?:foregroundStyle|foregroundColor|tint|fill|stroke|background)\()\.('+named_colors+r')\b',r'\1.white',s)
    # Use editable native text rather than embedding CHZ artwork or a screenshot.
    s=re.sub(r'Image\("(?:InjectCHZLogo|ExternalCHZLogo)"\)\s*\.resizable\(\)', 'ExternalCheatsWordmark()', s)
    s=s.replace('.preferredColorScheme(lightMode ? .light : .dark)', '.preferredColorScheme(.dark)')
    s=s.replace('.preferredColorScheme(darkMode ? .dark : .light)', '.preferredColorScheme(.dark)')
    path.write_text(s)

app=app_path.read_text()
start=app.index('                        Button(action: validate) {',app.index('struct LicenseLoginView: View'))
end=app.index('                        .buttonStyle(.plain)',start)
button=app[start:end].replace('ProgressView().tint(.white)','ProgressView().tint(.black)')
button=button.replace('.foregroundStyle(Color.white)','.foregroundStyle(Color.black)')
app=app[:start]+button+app[end:]
# Black thumb on white ON track keeps the switch state discernible in the monochrome palette.
anchor='        WindowGroup {\n'
assert anchor in app
app=app.replace('.environmentObject(appState)', '.saturation(0)\n                .tint(.white)\n                .onAppear { UISwitch.appearance().thumbTintColor = UIColor.black }\n                .environmentObject(appState)',1)
app=app.replace('.frame(width: 176, height: 116)', '.frame(width: 240, height: 116)')
app+='''
struct ExternalCheatsWordmark: View {
    var body: some View {
        VStack(spacing: 4) {
            Text("EXTERNAL").font(.system(size: 29, weight: .black, design: .rounded)).tracking(2.4)
            Text("CHEATS").font(.system(size: 16, weight: .semibold, design: .rounded)).tracking(6)
            Rectangle().fill(Color.white.opacity(0.35)).frame(width: 58, height: 1).padding(.top, 8)
        }
        .foregroundStyle(.white)
        .lineLimit(1).minimumScaleFactor(0.75)
        .accessibilityElement(children: .ignore).accessibilityLabel("EXTERNAL CHEATS")
    }
}
'''
assert login_logic in app, 'Authentication methods must stay byte-for-byte unchanged'
app_path.write_text(app)

path=root/'views/PatchProjectsView.swift'
s=path.read_text()
s=s.replace('category == item ? .white : secondaryText','category == item ? .black : secondaryText')
s=re.sub(r'private var fg: Color \{[^\n]+\}', 'private var fg: Color { .white }',s)
s=re.sub(r'private var muted: Color \{[^\n]+\}', 'private var muted: Color { Color.white.opacity(0.6) }',s)
s=re.sub(r'private var primaryText: Color \{[^\n]+\}', 'private var primaryText: Color { .white }',s)
s=re.sub(r'private var secondaryText: Color \{[^\n]+\}', 'private var secondaryText: Color { Color.white.opacity(0.6) }',s)
# Remove legacy rainbow theme selector; this product has one deliberate black/white theme.
a=s.index('    private var themeDots: some View {')
b=s.index('    @ViewBuilder\n    private var mainContent:',a)
s=s[:a]+'    private var themeDots: some View { EmptyView() }\n\n'+s[b:]
# The game-card arrow is placed on a solid white circle.
s=s.replace('Image(systemName: "arrow.right").font(.system(size: 12, weight: .bold)).foregroundStyle(.white)',
            'Image(systemName: "arrow.right").font(.system(size: 12, weight: .bold)).foregroundStyle(.black)')
path.write_text(s)

icon=root/'Assets.xcassets/AppIcon.appiconset'
icon.mkdir(parents=True,exist_ok=True)
shutil.copyfile(repo/'resources/external-cheats-icon-1024.png',icon/'ExternalCheatsIcon.png')
(icon/'Contents.json').write_text(json.dumps({'images':[{'filename':'ExternalCheatsIcon.png','idiom':'universal','platform':'ios','size':'1024x1024'}],'info':{'author':'xcode','version':1}},indent=2)+'\n')
for old in ['ExternalCHZLogo.imageset','InjectCHZLogo.imageset']:
    folder=root/'Assets.xcassets'/old
    if folder.exists(): shutil.rmtree(folder)

info_path=root/'Info.plist'
values=plistlib.loads(info_path.read_bytes())
bundle_id=values.get('CFBundleIdentifier')
values['CFBundleDisplayName']=brand
values['CFBundleName']='ExternalCheats'
assert values.get('CFBundleIdentifier')==bundle_id
info_path.write_bytes(plistlib.dumps(values,sort_keys=False))
project=root.parent/'ThreeOneOSFive.xcodeproj/project.pbxproj'
s=project.read_text()
s=re.sub(r'INFOPLIST_KEY_CFBundleDisplayName = [^;]+;', 'INFOPLIST_KEY_CFBundleDisplayName = "EXTERNAL CHEATS";',s)
s=re.sub(r'INFOPLIST_KEY_CFBundleName = [^;]+;', 'INFOPLIST_KEY_CFBundleName = ExternalCheats;',s)
s,count=re.subn(r'PRODUCT_NAME = injectchz;', 'PRODUCT_NAME = ExternalCheats;',s)
assert count>0
project.write_text(s)

app_after=app_path.read_text();patch_after=path.read_text()
after_lines=[line.strip() for line in (app_after+'\n'+patch_after).splitlines()
             if any(marker in line for marker in ['request.setValue(', 'request.httpBody =', 'URLSession.shared.data(', 'DevicePatchService.apply(', 'DevicePatchService.restore(', 'LicenseAPI.validate('])]
assert protected_lines==after_lines, 'API requests and real patch operations must not be altered'
assert 'ExternalCheatsWordmark()' in app_after
assert 'product: "EXTERNAL CHEATS"' in app_after
print('EXTERNAL CHEATS branding and black/white palette applied; login, API requests and patch operations preserved.')
