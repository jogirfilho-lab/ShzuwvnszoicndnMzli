
private enum PatchAssetService {
    static func prepare(fileName: String, downloadURL: String?, sha256: String?, sizeBytes: Int?) async throws -> URL {
        let safeName = (fileName as NSString).lastPathComponent
        guard safeName == fileName, !safeName.isEmpty, safeName != ".", safeName != ".." else {
            throw NSError(domain: "PatchAsset", code: 1, userInfo: [NSLocalizedDescriptionKey: "Nome de arquivo inválido."])
        }
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("RemotePatches", isDirectory: true)
        let local = dir.appendingPathComponent(safeName)
        if let sha256, !sha256.isEmpty, FileManager.default.fileExists(atPath: local.path) {
            let reusable = await Task.detached(priority: .userInitiated) {
                guard let data = try? Data(contentsOf: local), sizeBytes == nil || data.count == sizeBytes else { return false }
                let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
                return digest.caseInsensitiveCompare(sha256) == .orderedSame
            }.value
            if reusable { return local }
        }
        guard let downloadURL, let url = URL(string: downloadURL), url.scheme == "https" else {
            throw NSError(domain: "PatchAsset", code: 2, userInfo: [NSLocalizedDescriptionKey: "Arquivo não disponível na API."])
        }
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try await Task.detached(priority: .userInitiated) {
            if let sizeBytes, data.count != sizeBytes { throw NSError(domain: "PatchAsset", code: 3, userInfo: [NSLocalizedDescriptionKey: "Tamanho do arquivo não corresponde ao catálogo."]) }
            if let sha256, !sha256.isEmpty {
                let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
                guard digest.caseInsensitiveCompare(sha256) == .orderedSame else { throw NSError(domain: "PatchAsset", code: 4, userInfo: [NSLocalizedDescriptionKey: "Integridade do arquivo não corresponde ao catálogo."]) }
            }
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            try data.write(to: local, options: .atomic)
            return local
        }.value
    }
}

private func patchFileSubtitle(title: String, fileName: String, category: String) -> String {
    let normalized = title.folding(options: [.diacriticInsensitive, .caseInsensitive], locale: Locale(identifier: "pt_BR")).uppercased()
    var labels: [String] = []
    if normalized.contains("PESCO") { labels.append("pescoço") }
    if normalized.contains("PEITO") { labels.append("peito") }
    if normalized.contains("ALTO") { labels.append("alto") }
    if normalized.contains("ANTENA") { labels.append("antena") }
    if normalized.contains("BYPASS") { labels.append("bypass") }
    if normalized.contains("100%") { labels.append("100%") }
    let reference = labels.isEmpty ? fileName : labels.joined(separator: " + ")
    return "\(category) · referência: \(reference)"

}

private struct PatchPackageDetailsView: View {
    let title: String
    let fileName: String
    let downloadURL: String?
    let sha256: String?
    let sizeBytes: Int?
    @Environment(\.dismiss) private var dismiss
    @State private var project: PatchProject?
    @State private var error: String?
    var body: some View {
        NavigationStack {
            List {
                Section("ARQUIVO PUBLICADO") {
                    LabeledContent("Nome", value: title)
                    LabeledContent("Arquivo", value: fileName)
                    if let sizeBytes { LabeledContent("Tamanho", value: ByteCountFormatter.string(fromByteCount: Int64(sizeBytes), countStyle: .file)) }
                    if let sha256 { Text("SHA-256: \(sha256)").font(.caption.monospaced()).textSelection(.enabled) }
                }
                if let project {
                    Section("PACOTE .3105") {
                        LabeledContent("Projeto", value: project.name)
                        LabeledContent("Autor", value: project.author.isEmpty ? "Não informado" : project.author)
                        LabeledContent("Substituições", value: String(project.rules.count))
                        LabeledContent("Diretórios", value: String(project.directories.count))
                    }
                    if !project.isPrivate {
                        Section("APLICATIVOS ALVO") {
                            ForEach(project.allBundleIdentifiers, id: \.self) { Text($0).font(.caption.monospaced()) }
                        }
                        Section("PARTES DO ARQUIVO") {
                            ForEach(project.rules) { rule in
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(rule.replacementFilename).font(.headline)
                                    Text("Alvo: \(rule.bundleID)").font(.caption.monospaced())
                                    Text("Caminho: \(rule.relativePath)").font(.caption.monospaced())
                                    Text("\(rule.replacementData.count) bytes de substituição").font(.caption)
                                }
                            }
                            ForEach(project.directories) { directory in
                                Text("Diretório: \(directory.bundleID) / \(directory.relativePath)").font(.caption.monospaced())
                            }
                        }
                    } else {
                        Text("Conteúdo privado: caminhos internos não são expostos.").font(.caption)
                    }
                    Text("As informações acima vêm do pacote. O nome do recurso não comprova seu efeito no jogo.").font(.caption).foregroundStyle(.secondary)
                } else if let error {
                    Text(error).foregroundStyle(.red)
                } else {
                    ProgressView("Lendo informações do pacote…")
                }
            }
            .navigationTitle("Detalhes do arquivo")
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Fechar") { dismiss() } } }
            .task {
                do {
                    let local = try await PatchAssetService.prepare(fileName: fileName, downloadURL: downloadURL, sha256: sha256, sizeBytes: sizeBytes)
                    let decoded = try await Task.detached(priority: .userInitiated) {
                        let data = try PatchProjectLibrary.readPackage(at: local)
                        return try PatchPackageCodec.decode(data, password: nil)
                    }.value
                    project = decoded.project
                } catch {
                    self.error = error.localizedDescription
                }
            }
        }.preferredColorScheme(.dark)
    }
}
