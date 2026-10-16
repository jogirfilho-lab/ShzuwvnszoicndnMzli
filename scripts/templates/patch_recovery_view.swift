
private enum PatchRecoveryNotifications {
    static let show = Notification.Name("ExternalCheatsShowPatchRecovery")
    static let changed = Notification.Name("ExternalCheatsPatchTransactionsChanged")
}

private func patchOperationMessage(_ error: Error) -> String {
    guard let error = error as? PatchPackageError else { return error.localizedDescription }
    switch error {
    case .targetOccupied(let path):
        return "Este arquivo já está em uso por outro patch:\n\(path)\n\nAbra Patches ativos e restaure o patch anterior antes de ativar este. Recursos que substituem o mesmo arquivo não podem ficar ativos juntos."
    case .projectAlreadyApplied:
        return "Este patch já está registrado como ativo. Abra Patches ativos para conferir e restaurar a aplicação anterior."
    case .restoreTargetsChanged:
        return "O jogo ou outro processo alterou os arquivos depois da aplicação. A restauração não foi forçada para evitar sobrescrever arquivos diferentes. Os registros e backups foram preservados."
    case .restoreFailed:
        return "Não foi possível verificar ou restaurar este backup. Ele pode estar incompleto ou pertencer a uma instalação anterior do jogo. Nenhum registro foi apagado."
    default:
        return error.localizedDescription
    }
}

private struct PatchRecoveryView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var items: [PatchRecoveryItem] = []
    @State private var loading = true
    @State private var restoring = false
    @State private var pending: PatchRecoveryItem?
    @State private var confirmRestore = false
    @State private var errorMessage: String?
    @State private var restoredMessage: String?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Os registros abaixo são lidos dos backups deste aplicativo, inclusive os criados antes desta atualização. Restaure o patch anterior para liberar o arquivo ocupado.")
                    Text("Recursos que alteram o mesmo arquivo são alternativas, não funções cumulativas.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                if loading { ProgressView("Lendo registros…") }
                if let restoredMessage { Section { Text(restoredMessage).foregroundStyle(.white) } }
                if items.isEmpty && !loading && errorMessage == nil {
                    Section { Text("Nenhum patch ativo ou recuperação pendente foi encontrado neste aplicativo.") }
                }
                ForEach(items) { item in
                    Section {
                        Text("Projeto \(item.receipt.projectID.uuidString.prefix(8))")
                            .font(.headline)
                        Text(item.prepared ? "Aplicação interrompida — backup pendente" : "Patch registrado como aplicado")
                            .font(.caption).foregroundStyle(.secondary)
                        Text(item.createdAt.formatted(date: .abbreviated, time: .shortened))
                            .font(.caption).foregroundStyle(.secondary)
                        Text("\(item.targets.count) arquivo(s) afetado(s)")
                        ForEach(item.targets, id: \.self) { target in
                            Text(target).font(.caption.monospaced()).textSelection(.enabled)
                        }
                        Button {
                            pending = item
                            confirmRestore = true
                        } label: {
                            Label("Restaurar original e liberar arquivo", systemImage: "arrow.uturn.backward")
                        }.disabled(restoring)
                    }
                }
                if let errorMessage {
                    Section("NÃO FOI POSSÍVEL CONCLUIR") { Text(errorMessage).font(.callout) }
                }
            }
            .navigationTitle("Patches ativos")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Fechar") { dismiss() }.disabled(restoring)
                }
                ToolbarItem(placement: .primaryAction) {
                    Button { Task { await reload() } } label: { Image(systemName: "arrow.clockwise") }
                        .disabled(restoring)
                }
            }
            .interactiveDismissDisabled(restoring)
            .preferredColorScheme(.dark).tint(.white)
            .task { await reload() }
            .confirmationDialog("Restaurar este patch?", isPresented: $confirmRestore, titleVisibility: .visible) {
                Button("Restaurar \(pending?.targets.count ?? 0) arquivo(s) do backup", role: .destructive) {
                    guard let item = pending else { return }
                    Task { await restore(item) }
                }
                Button("Cancelar", role: .cancel) { pending = nil }
            } message: {
                Text("Será restaurado o original dos arquivos listados no projeto \(pending?.receipt.projectID.uuidString.prefix(8) ?? ""). O patch anterior será desativado. O backup não será apagado, e alterações posteriores do jogo não serão sobrescritas à força.")
            }
        }
    }
    @MainActor private func reload() async {
        loading = true
        defer { loading = false }
        do {
            items = try await Task.detached(priority: .userInitiated) {
                try DevicePatchService.recoveryItems()
            }.value
            errorMessage = nil
        } catch { errorMessage = patchOperationMessage(error) }
    }
    @MainActor private func restore(_ item: PatchRecoveryItem) async {
        restoring = true
        errorMessage = nil
        defer { restoring = false }
        do {
            try await Task.detached(priority: .userInitiated) {
                try DevicePatchService.restore(receipt: item.receipt)
            }.value
            restoredMessage = "Original restaurado. Agora você pode ativar outro recurso para esse arquivo."
            await reload()
        } catch { errorMessage = patchOperationMessage(error) }
    }
}
