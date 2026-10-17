"""English UI and supplied animated key-screen artwork; server contract stays untouched."""
from pathlib import Path
import base64,json,plistlib,re,sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parent.parent
translations=json.loads((repo/'scripts/english_ui_translations.json').read_text())
app=root/'App.swift';before=app.read_text()
markers=['request.setValue(', 'request.httpBody =', 'URLSession.shared.data(', 'DevicePatchService.apply(', 'DevicePatchService.restore(', 'LicenseAPI.validate(', 'static let storageKey', '@AppStorage', 'URL(string: "https://']
protected=lambda s:[line.strip() for line in s.splitlines() if any(m in line for m in markers)]
original_protected={str(p.relative_to(root)):protected(p.read_text()) for p in root.rglob('*.swift')}
start=before.index('    var body: some View {',before.index('struct LicenseLoginView: View {'))
end=before.index('    private func validateStoredKey()',start)
s=before[:start]+(repo/'scripts/templates/english_key_body.swift').read_text()+before[end:]
assert s[s.index('    private func validateStoredKey()',s.index('struct LicenseLoginView: View {')):]==before[end:]
if 'import ImageIO' not in s:s='import ImageIO\n'+s
header=(repo/'scripts/templates/english_key_header.swift').read_text().replace('@@HEADER_GIF_BASE64@@',base64.b64encode((repo/'resources/external-cheats-key-header.gif').read_bytes()).decode())
s+=header
app.write_text(s)

# Only replace complete, explicitly inventoried UI strings. Never rewrite substrings in paths or HTTP values.
literal=re.compile(r'"(?:[^"\\]|\\.)*"')
count=0
for p in root.rglob('*.swift'):
 text=p.read_text()
 def translate(m):
  global count
  raw=m.group()[1:-1]
  if raw in translations:
   count+=1
   return '"'+translations[raw]+'"'
  return m.group()
 text=literal.sub(translate,text)
 text=text.replace('Locale(identifier: "pt_BR")','Locale(identifier: "en_US")')
 text=text.replace('Locale(identifier: "pt-BR")','Locale(identifier: "en_US")')
 p.write_text(text)

s=app.read_text()
s=s.replace('        // Integrity monitor disabled for the signed production build.',
 '''        UserDefaults.standard.set("en", forKey: AppLanguage.storageKey)
        UserDefaults.standard.set(["en"], forKey: "AppleLanguages")
        // Integrity monitor disabled for the signed production build.''',1)
s=s.replace('        AppLanguage(rawValue: languageCode) ?? .english','        .english',1)
app.write_text(s)
localization=root/'helpers/Localization.swift';s=localization.read_text()
s=s.replace('enum AppLanguage: String, CaseIterable, Identifiable {','enum AppLanguage: String, CaseIterable, Identifiable {\n    static let allCases: [AppLanguage] = [.english]',1)
s=s.replace('var locale: Locale { Locale(identifier: rawValue) }','var locale: Locale { Locale(identifier: "en") }',1)
s=s.replace('Bundle.main.path(forResource: rawValue, ofType: "lproj")','Bundle.main.path(forResource: "en", ofType: "lproj")',1)
localization.write_text(s)
english=(root/'en.lproj/Localizable.strings').read_bytes()
for p in root.glob('*.lproj/Localizable.strings'):p.write_bytes(english)
info=root/'Info.plist';values=plistlib.loads(info.read_bytes());values['CFBundleDevelopmentRegion']='en';values['CFBundleLocalizations']=['en'];info.write_bytes(plistlib.dumps(values,sort_keys=False))
# Runtime API validation messages are presented in English without changing the response model.
server={
 'Chave válida':'Valid access key',
 'Chave inválida':'Invalid access key',
 'Chave expirada':'This access key has expired',
 'Chave revogada':'This access key has been revoked',
 'Chave bloqueada':'This access key is blocked',
 'Chave não encontrada':'Access key not found',
 'Limite de dispositivos atingido':'Device limit reached',
 'Serviço temporariamente indisponível':'Service temporarily unavailable',
}
for k,v in translations.items():
 if '\\(' not in k and '\\(' not in v:server[k]=v
mapping='\n'.join('        '+json.dumps(k,ensure_ascii=False)+': '+json.dumps(v,ensure_ascii=False)+',' for k,v in server.items())
s=app.read_text()+'''\nprivate func englishUIMessage(_ message: String) -> String {
    let translations: [String: String] = {
        return [
'''+mapping+'''
        ]
    }()
    return translations[message] ?? message
}
'''
app.write_text(s)
for p in root.rglob('*.swift'):
 key=str(p.relative_to(root))
 assert protected(p.read_text())==original_protected[key],f'API/storage/patch contract unexpectedly changed: {key}'
assert 'ExternalCheatsKeyHeader()' in app.read_text()
assert 'Text("ACCESS KEY")' in app.read_text() and 'Text("SIGN IN")' in app.read_text()
assert 'throw PatchPackageError.targetOccupied(' in (root/'helpers/PatchTransaction.swift').read_text()
assert 'LicenseStore.save(candidate, response: result)' in app.read_text()
print(f'English edition ready: {count} UI literals translated; animated key header installed; API, storage, patch operations and recovery retained.')
