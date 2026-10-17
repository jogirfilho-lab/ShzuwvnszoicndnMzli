from pathlib import Path
import base64,json,plistlib,re,sys
root=Path(sys.argv[1]);app=(root/'App.swift').read_text();view=(root/'views/PatchProjectsView.swift').read_text()
assert 'Text("ACCESS KEY")' in app
assert 'Text("SIGN IN")' in app
assert 'ExternalCheatsKeyHeader()' in app
assert 'CGImageSourceCreateWithData' in app and 'image.startAnimating()' in app
assert 'if reduceMotion' in app
assert 'LicenseAPI.validate(key: candidate)' in app
assert 'LicenseStore.save(candidate, response: result)' in app
assert 'onSuccess()' in app
assert 'Text("CHAVE DE ACESSO")' not in app and 'Text("ENTRAR")' not in app
assert 'static let allCases: [AppLanguage] = [.english]' in (root/'helpers/Localization.swift').read_text()
assert 'Patches ativos • Restaurar anteriores' not in view
assert 'PatchRecoveryView()' in view
assert 'RemotePatchAPI.fetchCatalog()' in view
assert 'private func loadCatalog() async' in view
assert 'request.httpBody = try JSONSerialization.data' in view
assert 'URLSession.shared.data(for: request)' in view
assert 'throw PatchPackageError.targetOccupied(' in (root/'helpers/PatchTransaction.swift').read_text()
info=plistlib.loads((root/'Info.plist').read_bytes())
assert info['CFBundleDisplayName']=='EXTERNAL CHEATS'
assert info['CFBundleDevelopmentRegion']=='en'
assert info['CFBundleLocalizations']==['en']
assert 'InjectLicenseClock' in app
print('PASS: English key controls, animated reference, English localization, API authentication, countdown, catalog and safe recovery verified.')
