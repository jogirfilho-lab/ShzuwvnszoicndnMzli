"""Expose real persisted receipts; never bypass target occupancy or force restoration."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);repo=Path(__file__).resolve().parent.parent
engine=root/'helpers/PatchTransaction.swift'
s=engine.read_text()
assert 'static func recoveryItems(' not in s
assert 'throw PatchPackageError.targetOccupied(' in s
engine.write_text(s+(repo/'scripts/templates/patch_recovery_engine.swift').read_text())

service=root/'helpers/DevicePatchService.swift';s=service.read_text()
s=s.replace('enum DevicePatchService {','enum DevicePatchService {\n    private static let mutationLock = NSRecursiveLock()\n',1)
for anchor in ['    static func apply(project: PatchProject) throws -> PatchTransactionReceipt {',
               '    static func inspectRestore(receipt: PatchTransactionReceipt) throws -> PatchRestoreInspection {',
               '    ) throws {']:
    assert anchor in s
    s=s.replace(anchor,anchor+'\n        mutationLock.lock()\n        defer { mutationLock.unlock() }')
s=s.replace('    static func latestReceipt(projectID: UUID) -> PatchTransactionReceipt? {',
    '    static func latestReceipt(projectID: UUID) -> PatchTransactionReceipt? {\n        mutationLock.lock()\n        defer { mutationLock.unlock() }',1)
# Post on successful completion only; restoration still uses the original strict engine.
start=s.index('    static func restore(');end=s.index('    static func resetToAppliedState(',start)
block=s[start:end]
assert block.endswith('    }\n\n')
block=block[:-len('    }\n\n')]+'        NotificationCenter.default.post(name: Notification.Name("ExternalCheatsPatchTransactionsChanged"), object: nil)\n    }\n\n'
s=s[:start]+block+s[end:]
s+='''
extension DevicePatchService {
    static func recoveryItems() throws -> [PatchRecoveryItem] {
        mutationLock.lock()
        defer { mutationLock.unlock() }
        return try PatchTransaction.recoveryItems(backupRoot: PatchProjectLibrary.backupRootURL())
    }
}
'''
service.write_text(s)

view=root/'views/PatchProjectsView.swift';s=view.read_text()
for name in ['struct PatchProjectsView: View {','private struct CompactPatchCard: View {','struct ExternalPanelView: View {']:
    assert name in s,name
    s=s.replace(name,name+'\n    @State private var showPatchRecovery = false',1)
s=s.replace('                    if videoGameSelected {','''                    Button { showPatchRecovery = true } label: {
                        Label("Patches ativos • Restaurar anteriores", systemImage: "arrow.uturn.backward.circle")
                            .font(.system(size: 12, weight: .semibold)).foregroundStyle(.white)
                    }.buttonStyle(.bordered).tint(.white)
                    if videoGameSelected {''',1)
start=s.index('struct PatchProjectsView: View {')
anchor='        .navigationBarHidden(true)'
pos=s.index(anchor,start)
s=s[:pos]+s[pos:].replace(anchor,anchor+'\n        .sheet(isPresented: $showPatchRecovery) { PatchRecoveryView() }',1)
s=s.replace('        .onAppear { synchronizeAppliedState() }','''        .onAppear { synchronizeAppliedState() }
        .sheet(isPresented: $showPatchRecovery) { PatchRecoveryView() }
        .onReceive(NotificationCenter.default.publisher(for: PatchRecoveryNotifications.changed).receive(on: RunLoop.main)) { _ in synchronizeAppliedState() }''',1)
s=s.replace('            Button("OK", role: .cancel) { alertMessage = nil }',
            '            Button("Gerenciar patches ativos") { alertMessage = nil; showPatchRecovery = true }\n            Button("OK", role: .cancel) { alertMessage = nil }',1)
s=s.replace('guard let projectID = findAppliedProjectID() else { return }',
            'guard let projectID = findAppliedProjectID() else { activeReceipt = nil; isActive = false; return }',1)
s=s.replace('guard let receipt = findExternalReceipt(patch) else { return }',
            'guard let receipt = findExternalReceipt(patch) else { receipts.removeValue(forKey: patch.id); if let index = patches.firstIndex(where: { $0.id == patch.id }) { patches[index].enabled = false }; return }',1)
start=s.index('struct ExternalPanelView: View {')
anchor='        .onDisappear { fpsMonitor.stop() }'
pos=s.index(anchor,start)
s=s[:pos]+s[pos:].replace(anchor,anchor+'''\n        .sheet(isPresented: $showPatchRecovery) { PatchRecoveryView() }
        .onReceive(NotificationCenter.default.publisher(for: PatchRecoveryNotifications.changed).receive(on: RunLoop.main)) { _ in
            for patch in patches { synchronizeExternalState(patch) }
        }''',1)
s=s.replace('            Button("OK", role: .cancel) { actionError = nil }',
            '            Button("Gerenciar patches ativos") { actionError = nil; showPatchRecovery = true }\n            Button("OK", role: .cancel) { actionError = nil }',1)
s=s.replace('.alert("Texturas", isPresented:', '.alert("Texturas", isPresented:',1)
needle='{ Button("OK", role: .cancel) { actionError = nil } } message:'
s=s.replace(needle,'{ Button("Gerenciar patches ativos") { actionError = nil; showPatchRecovery = true }; Button("OK", role: .cancel) { actionError = nil } } message:',1)
s=s.replace('alertMessage = error.localizedDescription','alertMessage = patchOperationMessage(error)')
s=s.replace('actionError = error.localizedDescription','actionError = patchOperationMessage(error)')
s+=(repo/'scripts/templates/patch_recovery_view.swift').read_text()
assert 'Patches ativos • Restaurar anteriores' in s
assert 'allowChangedTargets: true' not in s
assert 'throw PatchPackageError.targetOccupied(' in engine.read_text()
view.write_text(s)
print('Safe persisted-patch recovery added; occupancy protection and backup verification retained.')
