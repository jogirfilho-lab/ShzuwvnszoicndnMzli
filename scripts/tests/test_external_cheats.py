"""Validate branding and authentication invariants in generated production Swift."""
from pathlib import Path
import json, plistlib, re, sys
root=Path(sys.argv[1])
app=(root/'App.swift').read_text()
patches=(root/'views/PatchProjectsView.swift').read_text()
content=(root/'ContentView.swift').read_text()
info=plistlib.loads((root/'Info.plist').read_bytes())
assert info['CFBundleDisplayName']=='EXTERNAL CHEATS'
assert info['CFBundleName']=='ExternalCheats'
assert 'product: "EXTERNAL CHEATS"' in app
assert 'row("Produto", value: "EXTERNAL CHEATS")' in app
assert 'struct ExternalCheatsWordmark: View' in app
assert 'Text("EXTERNAL")' in app and 'Text("CHEATS")' in app
assert 'LicenseAPI.validate(key: candidate)' in app
assert 'LicenseStore.save(candidate, response: result)' in app
assert 'onSuccess()' in app
assert 'TimelineView(.periodic(from: .now, by: 1))' in app
assert 'ExternalPanelView(gameFilter: selectedGameID)' in patches
assert 'DevicePatchService.apply(project: decoded.project)' in patches
assert 'DevicePatchService.restore(receipt: receipt)' in patches
assert 'PatchPackageDetailsView' in patches
assert '[AppSection.home, .patches, .textures]' in content
assert '.foregroundStyle(Color.black)' in app[app.index('Button(action: validate)'):app.index('.buttonStyle(.plain)',app.index('Button(action: validate)'))]
for path in root.rglob('*.swift'):
    code=path.read_text()
    literals=re.findall(r'"(?:[^"\\]|\\.)*"',code)
    for literal in literals:
        assert not any(old in literal for old in ['CHZ Project','Project CHZ','Projeto CHZ','CHZ CHEATS','EXTERNAL CHZ','inject chz']), (path.name,literal[:80])
    assert not re.search(r'Color\.(red|green|blue|orange|yellow|pink|purple|cyan|mint|indigo|brown|teal)\b',code),path
    assert not re.search(r'Color\(\s*red:',code),path
for old in ['InjectCHZLogo.imageset','ExternalCHZLogo.imageset']:
    assert not (root/'Assets.xcassets'/old).exists()
icon=json.loads((root/'Assets.xcassets/AppIcon.appiconset/Contents.json').read_text())
assert icon['images'][0]['filename']=='ExternalCheatsIcon.png'
assert (root/'Assets.xcassets/AppIcon.appiconset/ExternalCheatsIcon.png').stat().st_size>0
print('EXTERNAL CHEATS identity, monochrome palette, API gate, live clock and patch operations verified.')
