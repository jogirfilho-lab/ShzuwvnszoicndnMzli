import Foundation

@main struct PatchRecoveryTests {
    static func require(_ condition: Bool, _ message: String) {
        if !condition { fatalError(message) }
    }
    static func sameReceipt(_ lhs: PatchTransactionReceipt, _ rhs: PatchTransactionReceipt) -> Bool {
        lhs.id == rhs.id && lhs.projectID == rhs.projectID &&
        PatchPathValidator.canonicalFileURL(lhs.journalURL).path == PatchPathValidator.canonicalFileURL(rhs.journalURL).path
    }
    static func main() throws {
        let root=FileManager.default.temporaryDirectory.appendingPathComponent("patch-recovery-tests-\(UUID().uuidString)")
        let container=root.appendingPathComponent("container")
        let backups=root.appendingPathComponent("backups")
        try FileManager.default.createDirectory(at: container.appendingPathComponent("Documents"), withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let bundle="com.example.testgame"
        func resolver(_ _: String) throws -> URL { container }
        func project(_ title: String, path: String="Documents/shared.bin") -> PatchProject {
            PatchProject(name: title, rules: [PatchRule(bundleID: bundle, relativePath: path, replacementFilename: "payload.bin", replacementData: Data(title.utf8))])
        }
        let target=container.appendingPathComponent("Documents/shared.bin")
        try Data("original".utf8).write(to: target)
        let a=project("A");let b=project("B")
        let receiptA=try PatchTransaction.apply(project: a, backupRoot: backups, containerResolver: resolver)
        do {
            _=try PatchTransaction.apply(project: b, backupRoot: backups, containerResolver: resolver)
            fatalError("Conflicting application must remain blocked")
        } catch PatchPackageError.targetOccupied { }
        var items=try PatchTransaction.recoveryItems(backupRoot: backups)
        print("Recovery test: found \(items.count) active item(s); expected \(receiptA.id)")
        for item in items { print("Found \(item.receipt.id): \(item.receipt.journalURL.path)") }
        print("Expected path: \(receiptA.journalURL.path)")
        require(items.count==1 && sameReceipt(items[0].receipt,receiptA),"Old active receipt must be discoverable")
        require(items[0].targets==[bundle+"/Documents/shared.bin"],"Recovery must list real affected targets")
        try PatchTransaction.restore(receipt: receiptA, containerResolver: resolver)
        require(try Data(contentsOf: target)==Data("original".utf8),"Restore must recover original bytes")
        require(FileManager.default.fileExists(atPath: receiptA.journalURL.path),"Recovery must preserve journal")
        items=try PatchTransaction.recoveryItems(backupRoot: backups)
        require(items.isEmpty,"Restored patches must disappear from active list")
        let receiptB=try PatchTransaction.apply(project: b, backupRoot: backups, containerResolver: resolver)
        require(try Data(contentsOf: target)==Data("B".utf8),"Restoring A must allow applying B")
        try Data("changed-by-game".utf8).write(to: target,options: .atomic)
        do {
            try PatchTransaction.restore(receipt: receiptB, containerResolver: resolver)
            fatalError("Changed targets must not be force overwritten")
        } catch PatchPackageError.restoreTargetsChanged { }
        require(try Data(contentsOf: target)==Data("changed-by-game".utf8),"Changed target must remain untouched")
        require(try PatchTransaction.recoveryItems(backupRoot: backups).count==1,"Failed restoration must keep active receipt")
        try Data("B".utf8).write(to: target,options: .atomic)
        let originalBackup=try FileManager.default.contentsOfDirectory(at: receiptB.journalURL.deletingLastPathComponent(),includingPropertiesForKeys:nil).first { $0.pathExtension=="original" }!
        try Data("corrupt".utf8).write(to: originalBackup)
        do {
            try PatchTransaction.restore(receipt: receiptB, containerResolver: resolver)
            fatalError("Corrupt backup must remain blocked")
        } catch PatchPackageError.restoreFailed { }
        require(try Data(contentsOf: target)==Data("B".utf8),"Corrupt backup must not modify target")
        let pendingTarget=container.appendingPathComponent("Documents/pending.bin")
        try Data("pending-original".utf8).write(to: pendingTarget)
        let c=project("C",path:"Documents/pending.bin")
        let receiptC=try PatchTransaction.apply(project:c,backupRoot:backups,containerResolver:resolver)
        var journal=try PropertyListSerialization.propertyList(from:Data(contentsOf:receiptC.journalURL),format:nil) as! [String:Any]
        journal["status"]="prepared"
        try PropertyListSerialization.data(fromPropertyList:journal,format:.binary,options:0).write(to:receiptC.journalURL)
        items=try PatchTransaction.recoveryItems(backupRoot:backups)
        require(items.contains { sameReceipt($0.receipt,receiptC) && $0.prepared },"Interrupted transaction must be offered for recovery")
        try PatchTransaction.restore(receipt:receiptC,containerResolver:resolver)
        require(try Data(contentsOf:pendingTarget)==Data("pending-original".utf8),"Interrupted transaction must restore original")
        let legacyTarget=container.appendingPathComponent("Documents/legacy.bin")
        try Data("legacy-original".utf8).write(to:legacyTarget)
        let legacy=project("legacy",path:"Documents/legacy.bin")
        let legacyReceipt=try PatchTransaction.apply(project:legacy,backupRoot:backups,containerResolver:resolver)
        journal=try PropertyListSerialization.propertyList(from:Data(contentsOf:legacyReceipt.journalURL),format:nil) as! [String:Any]
        journal["schemaVersion"]=1
        try PropertyListSerialization.data(fromPropertyList:journal,format:.binary,options:0).write(to:legacyReceipt.journalURL)
        require(try PatchTransaction.recoveryItems(backupRoot:backups).contains { sameReceipt($0.receipt,legacyReceipt) },"Legacy schema must remain supported")
        try PatchTransaction.restore(receipt:legacyReceipt,containerResolver:resolver)
        require(try Data(contentsOf:legacyTarget)==Data("legacy-original".utf8),"Legacy backup must remain restorable")
        print("PASS: conflict blocked; old receipts found; originals restored; next patch allowed; journals kept; changed/corrupt files protected; interrupted and legacy transactions recovered.")
    }
}
