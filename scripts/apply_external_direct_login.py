"""Remove calculator-only gate; preserve key authentication and set official app name."""
from pathlib import Path
import plistlib,re,sys
root=Path(sys.argv[1]);app=root/'App.swift';text=app.read_text()
start=text.index('    private func validateStoredKey()',text.index('struct LicenseLoginView: View {'))
end=text.index('\n}\n',start)
login=text[start:end]
assert '    @State private var calculatorUnlocked = false\n' in text
text=text.replace('    @State private var calculatorUnlocked = false\n','',1)
text=text.replace('.opacity(showOnboarding || !calculatorUnlocked || !isLicensed ? 0 : 1)', '.opacity(showOnboarding || !isLicensed ? 0 : 1)',1)
text=text.replace('.allowsHitTesting(!showOnboarding && calculatorUnlocked && isLicensed)', '.allowsHitTesting(!showOnboarding && isLicensed)',1)
start=text.index('                if !showOnboarding && !calculatorUnlocked {')
end=text.index('                if !showOnboarding && !isLicensed {',start)
text=text[:start]+text[end:]
start=text.index('private struct CalculatorGateView: View {')
end=text.index('private enum Branding {',start)
assert 'private struct CalculatorKey:' in text[start:end] and 'private struct CalculatorGlyph:' in text[start:end]
text=text[:start]+text[end:]
text=text.replace('private enum Branding { static let appName = "Nubank" }','private enum Branding { static let appName = "EXTERNAL" }',1)
assert login in text,'Key validation must stay unchanged'
assert 'CalculatorGateView' not in text and 'calculatorUnlocked' not in text
assert '.allowsHitTesting(!showOnboarding && isLicensed)' in text
assert 'LicenseStore.save(candidate, response: result)' in text
app.write_text(text)
info=root/'Info.plist';values=plistlib.loads(info.read_bytes());bundleID=values.get('CFBundleIdentifier')
values['CFBundleDisplayName']='EXTERNAL';values['CFBundleName']='External'
assert values.get('CFBundleIdentifier')==bundleID
info.write_bytes(plistlib.dumps(values,sort_keys=False))
project=root.parent/'ThreeOneOSFive.xcodeproj/project.pbxproj';s=project.read_text()
s,n=re.subn(r'INFOPLIST_KEY_CFBundleDisplayName = [^;]+;', 'INFOPLIST_KEY_CFBundleDisplayName = EXTERNAL;',s);assert n==2
s=re.sub(r'INFOPLIST_KEY_CFBundleName = [^;]+;', 'INFOPLIST_KEY_CFBundleName = External;',s)
s,n=re.subn(r'PRODUCT_NAME = ExternalCheats;', 'PRODUCT_NAME = External;',s);assert n==2
project.write_text(s)
print('PASS: calculator interface removed; EXTERNAL display/product names set; English, animated key screen and real key validation retained.')
