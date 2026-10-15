"""Final transformation: merged External, verified cache, real details, immediate feedback."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
repo = Path(__file__).resolve().parent.parent
p = root / 'views/PatchProjectsView.swift'
s = p.read_text()

def replace(old, new, count=1):
    global s
    assert old in s, 'Expected source marker missing: ' + old[:100]
    s = s.replace(old, new, count)

# Reuse the authenticated External panel in the EXTERNAL category instead of duplicating apply logic.
replace('''                        LazyVStack(spacing: 10) {
                            ForEach(videoVisibleFeatures)''', '''                        if videoCategory == "EXTERNAL" {
                            ExternalPanelView(gameFilter: selectedGameID).frame(minHeight: 520)
                        } else {
                        LazyVStack(spacing: 10) {
                            ForEach(videoVisibleFeatures)''')
replace('''                        Button { withAnimation(.easeInOut(duration: 0.2)) { videoGameSelected = false } }''', '''                        }
                        Button { videoGameSelected = false }''')
replace('subtitle: "Recurso pré-carregado do Free Fire.",', 'subtitle: patchFileSubtitle(title: patch.title, fileName: patch.fileName, category: patch.title.uppercased().contains("CACHE") ? "CACHE" : "AVATAR"),')
replace('''    private let texturesOnly: Bool
''', '''    private let texturesOnly: Bool
    private let gameFilter: String?
''')
replace('''init(initialCategory: String = "Funções", texturesOnly: Bool = false) {
        self.texturesOnly = texturesOnly''', '''init(initialCategory: String = "Funções", texturesOnly: Bool = false, gameFilter: String? = nil) {
        self.texturesOnly = texturesOnly
        self.gameFilter = gameFilter''')
replace('''            guard category != .profile else { return false }
            let raw''', '''            guard category != .profile else { return false }
            if let gameFilter {
                let base = patch.game.lowercased().split(separator: ":").first.map(String.init) ?? ""
                guard base == gameFilter || base == "online-" + gameFilter else { return false }
            }
            let raw''')
replace('ForEach(Category.allCases) { item in', 'ForEach(Category.allCases.filter { gameFilter == nil || $0 != .textures }) { item in')
# Main card immediate pending visual state, with actual success only from DevicePatchService receipt.
replace('''    @State private var activationToken = UUID()
''', '''    @State private var activationToken = UUID()
    @State private var showDetails = false
''')
replace('''Text(feature.subtitle).font(.system(size: 11, weight: .medium))''', '''Text(isWorking ? "Processando arquivo…" : feature.subtitle).font(.system(size: 11, weight: .medium))''')
replace('''            Toggle("", isOn: Binding(get: { isActive }, set: { on in''', '''            Button { showDetails = true } label: { Image(systemName: "info.circle").foregroundStyle(.gray) }
                .buttonStyle(.plain).accessibilityLabel("Detalhes do arquivo")
            Toggle("", isOn: Binding(get: { isActive || isWorking }, set: { on in''')
replace('''            .tint(Color.red)
        }
        .padding(.horizontal, 12)''', '''            .tint(Color.red)
            .disabled(isWorking)
            .transaction { $0.animation = nil }
        }
        .padding(.horizontal, 12)''')
replace('''        .onAppear { synchronizeAppliedState() }
''', '''        .onAppear { synchronizeAppliedState() }
        .sheet(isPresented: $showDetails) {
            PatchFileLookupView(patch: feature.patch)
        }
''')
replace('''                let data = try PatchProjectLibrary.readPackage(at: url)
                let decoded = try PatchPackageCodec.decode(data, password: nil)
                let receipt = try DevicePatchService.apply(project: decoded.project)''', '''                let receipt = try await Task.detached(priority: .userInitiated) {
                    let data = try PatchProjectLibrary.readPackage(at: url)
                    let decoded = try PatchPackageCodec.decode(data, password: nil)
                    return try DevicePatchService.apply(project: decoded.project)
                }.value''')
# Cache catalog briefly by validated key; never reuse it across sessions, revocation or expiry.
replace('''private enum RemotePatchAPI {
''', '''private enum RemotePatchAPI {
    @MainActor private static var cachedCatalog: [RemotePatchDescriptor]?
    @MainActor private static var catalogKey: String?
    @MainActor private static var catalogAt = Date.distantPast
''')
replace('''        guard let key = LicenseStore.storedKey else { return nil }
        do {''', '''        guard let key = LicenseStore.storedKey else { return nil }
        if let profile = LicenseStore.profileSnapshot,
           let raw = profile.expiresAt,
           let expiry = ISO8601DateFormatter().date(from: raw), expiry <= Date() { return nil }
        if catalogKey == key, Date().timeIntervalSince(catalogAt) < 10, let cachedCatalog { return cachedCatalog }
        do {''')
replace('''            return catalog.patches
        } catch { return nil }''', '''            cachedCatalog = catalog.patches
            catalogKey = key
            catalogAt = Date()
            return catalog.patches
        } catch { return nil }''')
a = s.index('    static func resolve(patch: PreloadedPatch) async -> URL? {')
b = s.index('\n}\nimport SwiftUI', a)
s = s[:a] + '''    static func descriptor(patch: PreloadedPatch) async -> RemotePatchDescriptor? {
        guard let catalog = await fetchCatalog() else { return nil }
        return catalog.first { $0.fileName.precomposedStringWithCanonicalMapping == patch.fileName.precomposedStringWithCanonicalMapping }
    }
    static func resolve(patch: PreloadedPatch) async -> URL? {
        guard let descriptor = await descriptor(patch: patch) else { return nil }
        return try? await PatchAssetService.prepare(fileName: descriptor.fileName,
            downloadURL: descriptor.downloadUrl, sha256: descriptor.sha256, sizeBytes: descriptor.sizeBytes)
    }
''' + s[b:]
replace('static func fetchCatalog() async', '@MainActor static func fetchCatalog() async')
replace('static func descriptor(patch: PreloadedPatch) async', '@MainActor static func descriptor(patch: PreloadedPatch) async')
replace('static func resolve(patch: PreloadedPatch) async', '@MainActor static func resolve(patch: PreloadedPatch) async')
# Add optional metadata already provided by server without changing backend.
replace('''    let downloadUrl: String?
    var interfaceTab''', '''    let downloadUrl: String?
    let sha256: String?
    let sizeBytes: Int?
    var interfaceTab''')
replace('''case id, title, game, fileName, downloadUrl, interfaceTab, section }''', '''case id, title, game, fileName, downloadUrl, sha256, sizeBytes, interfaceTab, section }''')
replace('''        downloadUrl = try? container.decode(String.self, forKey: .downloadUrl)
''', '''        downloadUrl = try? container.decode(String.self, forKey: .downloadUrl)
        sha256 = try? container.decode(String.self, forKey: .sha256)
        sizeBytes = try? container.decode(Int.self, forKey: .sizeBytes)
''')
replace('''    @State private var workingIDs: Set<Int> = []
''', '''    @State private var workingIDs: Set<Int> = []
    @State private var detailPatch: ExternalCatalogPatch?
''')
replace('''        .onDisappear { fpsMonitor.stop() }
''', '''        .onDisappear { fpsMonitor.stop() }
        .sheet(item: $detailPatch) { patch in
            PatchPackageDetailsView(title: patch.title, fileName: patch.fileName,
                downloadURL: patch.downloadUrl, sha256: patch.sha256, sizeBytes: patch.sizeBytes)
        }
''')
replace('''                Text(patch.title).font(.system(size: 13, weight: .semibold)).foregroundStyle(primaryText).lineLimit(1)
''', '''                Text(patch.title).font(.system(size: 13, weight: .semibold)).foregroundStyle(primaryText).lineLimit(1)
                Text(isWorking ? "Processando arquivo…" : patchFileSubtitle(title: patch.title, fileName: patch.fileName, category: category.rawValue))
                    .font(.system(size: 11)).foregroundStyle(secondaryText).lineLimit(2)
''')
replace('''            Toggle("", isOn: Binding(get: {
                patches.first''', '''            Button { detailPatch = patch } label: { Image(systemName: "info.circle").foregroundStyle(secondaryText) }
                .buttonStyle(.plain).accessibilityLabel("Detalhes do arquivo")
            Toggle("", isOn: Binding(get: {
                workingIDs.contains(patch.id) || patches.first''')
# Parenthesize nil-coalescing to keep Bool expression well-typed.
replace('''workingIDs.contains(patch.id) || patches.first(where: { $0.id == patch.id })?.enabled ?? false''', '''workingIDs.contains(patch.id) || (patches.first(where: { $0.id == patch.id })?.enabled ?? false)''')
replace('''            })).labelsHidden().tint(accent).scaleEffect(0.86)
''', '''            })).labelsHidden().tint(accent).scaleEffect(0.86)
                .disabled(isWorking).transaction { $0.animation = nil }
''')
a=s.index('                guard let remote = patch.downloadUrl',s.index('    private func applyExternal'))
b=s.index('                await MainActor.run {',a)
s=s[:a]+'''                let local = try await PatchAssetService.prepare(fileName: patch.fileName,
                    downloadURL: patch.downloadUrl, sha256: patch.sha256, sizeBytes: patch.sizeBytes)
                let receipt = try await Task.detached(priority: .userInitiated) {
                    let package = try PatchProjectLibrary.readPackage(at: local)
                    let decoded = try PatchPackageCodec.decode(package, password: nil)
                    return try DevicePatchService.apply(project: decoded.project)
                }.value
'''+s[b:]
s += (repo / 'scripts/templates/patch_asset_details.swift').read_text()
s += '''
private struct PatchFileLookupView: View {
    let patch: PreloadedPatch
    @State private var descriptor: RemotePatchDescriptor?
    @State private var finished = false
    var body: some View {
        Group {
            if let descriptor {
                PatchPackageDetailsView(title: patch.title, fileName: descriptor.fileName,
                    downloadURL: descriptor.downloadUrl, sha256: descriptor.sha256, sizeBytes: descriptor.sizeBytes)
            } else {
                VStack(spacing: 16) {
                    Text(finished ? "Arquivo não disponível no catálogo autorizado." : "Consultando informações do arquivo…")
                    if !finished { ProgressView() }
                }.padding(28)
            }
        }.task { descriptor = await RemotePatchAPI.descriptor(patch: patch); finished = true }
    }
}
'''
p.write_text(s)
# Remove only the standalone External navigation item. Its view remains accessible through Injetor.
p=root/'ContentView.swift';c=p.read_text()
assert '[AppSection.home, .patches, .external, .textures]' in c
c=c.replace('[AppSection.home, .patches, .external, .textures]', '[AppSection.home, .patches, .textures]')
p.write_text(c)
p=root/'helpers/AppTabNavigationState.swift';c=p.read_text()
assert '[.home, .patches, .external, .textures].filter(isVisible)' in c
c=c.replace('[.home, .patches, .external, .textures].filter(isVisible)', '[.home, .patches, .textures].filter(isVisible)')
c=c.replace('''        case .files:
            return developerModeEnabled''', '''        case .external:
            return false
        case .files:
            return developerModeEnabled''')
p.write_text(c)
print('External merged into Injetor; real package details and immediate pending feedback enabled.')
