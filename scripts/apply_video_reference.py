"""Apply the supplied video design after the legacy build transformations."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
patch = root / 'views/PatchProjectsView.swift'
t = patch.read_text()
start = t.index('struct PatchProjectsView: View')
body = t.index('    var body: some View {', start)
end = t.index('private var fg: Color', body)
old_body = t[body:end]
task = old_body[old_body.index('        .task {'):]
new_body = '''    @State private var videoGameSelected = false
    @State private var videoCategory = "AVATAR"

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 20) {
                    if videoGameSelected {
                        videoLogPanel
                        videoCategoryBar
                        HStack {
                            Text(videoCategory).font(.system(size: 12, weight: .bold, design: .monospaced))
                            Spacer()
                            Text("\\(videoVisibleFeatures.count) ITENS").font(.system(size: 10, design: .monospaced)).foregroundStyle(.gray)
                        }.foregroundStyle(.white)
                        LazyVStack(spacing: 10) {
                            ForEach(videoVisibleFeatures) { feature in
                                CompactPatchCard(feature: feature, store: store, darkMode: true)
                            }
                            if videoVisibleFeatures.isEmpty {
                                Text(remoteCatalog == nil ? "Carregando catálogo da API…" : "Nenhum recurso publicado nesta categoria.")
                                    .font(.system(size: 12)).foregroundStyle(.gray).padding(.vertical, 26)
                            }
                        }
                        Button { withAnimation(.easeInOut(duration: 0.2)) { videoGameSelected = false } } label: {
                            Label("Trocar edição", systemImage: "arrow.left.arrow.right")
                                .font(.system(size: 12, weight: .semibold)).foregroundStyle(.red)
                        }.buttonStyle(.plain)
                    } else {
                        videoSelectionHeader
                        Text("EDIÇÕES DISPONÍVEIS").font(.system(size: 10, weight: .bold, design: .monospaced)).foregroundStyle(.gray).tracking(1.5)
                        ForEach(preloadedGames) { game in videoGameCard(game) }
                        HStack(spacing: 7) {
                            Image(systemName: "shield.lefthalf.filled").foregroundStyle(.red)
                            Text("Acesso por key • Catálogo autenticado").foregroundStyle(.gray)
                        }.font(.system(size: 11)).frame(maxWidth: .infinity).padding(.top, 16)
                    }
                }.padding(.horizontal, 18).padding(.top, 20).padding(.bottom, 30)
            }
        }
        .preferredColorScheme(.dark)
        .navigationBarHidden(true)
'''
t = t[:body] + new_body + task + t[end:]
helpers = '''
    private func videoGroup(_ feature: CompactFeature) -> String {
        let title = feature.title.uppercased()
        if title.contains("CACHE") { return "CACHE" }
        if title.contains("HS") || title.contains("PESCO") || title.contains("AVATAR") { return "AVATAR" }
        return "EXTERNAL"
    }

    private var videoVisibleFeatures: [CompactFeature] {
        features.filter { videoGroup($0) == videoCategory }
    }

    private var videoSelectionHeader: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("CHZ CHEATS // GAME SELECT").font(.system(size: 10, weight: .bold, design: .monospaced)).foregroundStyle(.white)
                Spacer()
                Text("CHZ").font(.system(size: 18, weight: .black, design: .rounded)).italic().foregroundStyle(.red)
            }
            Text("Selecione o seu Free Fire").font(.system(size: 28, weight: .bold)).foregroundStyle(.white)
            Text("Selecione uma edição para continuar").font(.system(size: 13)).foregroundStyle(.gray)
            HStack(spacing: 6) {
                Circle().fill(remoteCatalog == nil ? Color.orange : Color.green).frame(width: 5, height: 5)
                Text(remoteCatalog == nil ? "CONECTANDO À API" : "CATÁLOGO RECEBIDO")
                    .font(.system(size: 9, weight: .bold, design: .monospaced)).foregroundStyle(remoteCatalog == nil ? Color.orange : Color.green)
                Spacer()
                Text("CHZ CHEATS").font(.system(size: 9, design: .monospaced)).foregroundStyle(.gray)
            }.padding(.vertical, 10)
        }
    }

    private func videoGameCard(_ game: PreloadedGame) -> some View {
        Button {
            selectedGameID = game.id
            withAnimation(.easeInOut(duration: 0.2)) { videoGameSelected = true }
        } label: {
            HStack(spacing: 14) {
                remoteLogo(url: logoURLs[game.id]).frame(width: 60, height: 60)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                VStack(alignment: .leading, spacing: 6) {
                    Text(game.id == "free-fire" ? "Free Fire" : "Free Fire Max").font(.system(size: 17, weight: .bold)).foregroundStyle(.white)
                    Text(game.id == "free-fire" ? "Edição principal" : "Edição expandida").font(.system(size: 11)).foregroundStyle(.gray)
                    Text("SELECIONAR EDIÇÃO").font(.system(size: 8, weight: .bold, design: .monospaced)).foregroundStyle(.red)
                        .padding(.horizontal, 7).padding(.vertical, 4).background(Color.red.opacity(0.13), in: Capsule())
                }
                Spacer(minLength: 2)
                Image(systemName: "arrow.right").font(.system(size: 12, weight: .bold)).foregroundStyle(.white)
                    .frame(width: 30, height: 30).background(Color.red, in: Circle())
            }.padding(15).frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(white: 0.065), in: RoundedRectangle(cornerRadius: 18))
                .overlay(RoundedRectangle(cornerRadius: 18).stroke(Color.red.opacity(0.5), lineWidth: 1))
                .shadow(color: .red.opacity(0.12), radius: 6)
        }.buttonStyle(.plain)
    }

    private var videoLogPanel: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("CHZ CHEATS // SYSTEM LOG").font(.system(size: 10, weight: .bold, design: .monospaced)).foregroundStyle(.green)
                Spacer()
                Circle().fill(remoteCatalog == nil ? Color.orange : Color.green).frame(width: 5, height: 5)
            }
            Text("CATÁLOGO DA API • \\(features.count) RECURSO(S)")
                .font(.system(size: 8, weight: .medium, design: .monospaced)).foregroundStyle(.gray)
            HStack(spacing: 8) {
                Image(systemName: "info.circle.fill").foregroundStyle(.red)
                Text(remoteCatalog == nil ? "Aguardando resposta do catálogo" : "Catálogo carregado • Selecione um recurso")
                    .font(.system(size: 11)).foregroundStyle(.white.opacity(0.8))
            }
        }.padding(14).frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(white: 0.055), in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(Color.red.opacity(0.5), lineWidth: 1))
    }

    private var videoCategoryBar: some View {
        HStack(spacing: 8) {
            ForEach(["AVATAR", "CACHE", "EXTERNAL"], id: \\.self) { group in
                Button { withAnimation(.easeInOut(duration: 0.15)) { videoCategory = group } } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(group).font(.system(size: 10, weight: .bold, design: .monospaced))
                        Text("\\(features.filter { videoGroup($0) == group }.count) funções").font(.system(size: 8))
                    }.foregroundStyle(videoCategory == group ? .white : .gray)
                        .frame(maxWidth: .infinity, alignment: .leading).padding(10)
                        .background(videoCategory == group ? Color.red.opacity(0.18) : Color(white: 0.065), in: RoundedRectangle(cornerRadius: 10))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.red.opacity(videoCategory == group ? 0.8 : 0.25), lineWidth: 1))
                }.buttonStyle(.plain)
            }
        }
    }

'''
t = t.replace('private var fg: Color', helpers + '    private var fg: Color', 1)
# Preserve existing apply/restore functions; only restyle the existing row.
card_start = t.index('private struct CompactPatchCard: View')
card_end = t.index('private struct RemotePatchDescriptor', card_start)
card = t[card_start:card_end]
card = card.replace('.foregroundStyle(darkMode ? .white : .black)', '.foregroundStyle(Color.white)')
card = card.replace('.foregroundStyle(Color.white)', '.foregroundStyle(Color.red)', 1)
card = re.sub(r'\.tint\([^\n]+\)', '.tint(Color.red)', card)
card = re.sub(r'\.background\(darkMode \? [^\n]+', '.background(Color(white: 0.065), in: RoundedRectangle(cornerRadius: 14, style: .continuous))', card)
card = re.sub(r'\.overlay\(RoundedRectangle\(cornerRadius: (?:14|16), style: \.continuous\)\.stroke\([^\n]+', '.overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.red.opacity(0.32), lineWidth: 1))', card)
t = t[:card_start] + card + t[card_end:]
patch.write_text(t)

content = root / 'ContentView.swift'
c = content.read_text()
# Replace the visible home section with the real profile, not simulated metrics.
c, count = re.subn(r'case \.home:\s*CHZHomeView\(\s*onOpenSettings: openSettings,\s*onOpenLogs: openLogs\s*\)', '''case .home:
            NavigationStack {
                Form { LicenseProfileView() }
                    .scrollContentBackground(.hidden)
                    .background(Color.black)
                    .navigationTitle("Licença")
                    .preferredColorScheme(.dark)
            }''', c, count=1)
assert count == 1, 'Home section marker missing'
compact = c.index('    private var compactLayout: some View {')
regular = c.index('    private var regularLayout: some View {', compact)
block = c[compact:regular]
if 'sectionContent(.home)' not in block:
    block = block.replace('TabView(selection: tabSelection) {', '''TabView(selection: tabSelection) {
    sectionContent(.home)
        .tabItem { CompactTabLabel(title: "Início", systemImage: "house.fill") }
        .tag(AppSection.home.rawValue)''', 1)
block = block.replace('title: "CHZ CHEATS", systemImage: "scope"', 'title: "Injetor", systemImage: "gamecontroller.fill"')
block = block.replace('title: "PROXY", systemImage: "scope"', 'title: "Injetor", systemImage: "gamecontroller.fill"')
c = c[:compact] + block + c[regular:]
c = c.replace('[AppSection.patches, .external, .textures]', '[AppSection.home, .patches, .external, .textures]')
content.write_text(c)
nav = root / 'helpers/AppTabNavigationState.swift'
n = nav.read_text().replace('[.patches, .external, .textures].filter(isVisible)', '[.home, .patches, .external, .textures].filter(isVisible)')
nav.write_text(n)
# Keep the license values honest: absent snapshot is not an active license.
app = root / 'App.swift'
a = app.read_text().replace('snapshot?.status ?? "VIP ATIVO"', 'snapshot?.status ?? "NÃO CONFIGURADA"')
app.write_text(a)
for marker in ['videoGameCard', 'videoLogPanel', 'videoCategoryBar', 'CompactPatchCard(feature: feature, store: store, darkMode: true)']:
    assert marker in patch.read_text(), marker
assert 'sectionContent(.home)' in content.read_text()
assert 'sectionContent(.textures)' in content.read_text()
assert 'AntiTamperGuard.start()' not in app.read_text()
print('Video reference applied; existing API/apply/restore functions retained.')
