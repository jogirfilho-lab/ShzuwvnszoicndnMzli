
struct PatchRecoveryItem: Identifiable {
    let receipt: PatchTransactionReceipt
    let createdAt: Date
    let targets: [String]
    let prepared: Bool
    var id: UUID { receipt.id }
}

extension PatchTransaction {
    static func recoveryItems(backupRoot: URL, fileManager: FileManager = .default) throws -> [PatchRecoveryItem] {
        guard fileManager.fileExists(atPath: backupRoot.path) else { return [] }
        let projects = try fileManager.contentsOfDirectory(at: backupRoot, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles])
        var items: [PatchRecoveryItem] = []
        for project in projects {
            guard let projectID = UUID(uuidString: project.lastPathComponent),
                  try project.resourceValues(forKeys: [.isDirectoryKey]).isDirectory == true else { continue }
            let transactions = try fileManager.contentsOfDirectory(at: project, includingPropertiesForKeys: [.isDirectoryKey], options: [.skipsHiddenFiles])
            for transaction in transactions {
                guard let transactionID = UUID(uuidString: transaction.lastPathComponent),
                      try transaction.resourceValues(forKeys: [.isDirectoryKey]).isDirectory == true else { continue }
                let journalURL = transaction.appendingPathComponent(journalFilename)
                guard fileManager.fileExists(atPath: journalURL.path) else { continue }
                // A corrupt existing record is an error, not permission to forget occupied files.
                let journal = try readJournal(journalURL)
                guard (minimumSchemaVersion...schemaVersion).contains(journal.schemaVersion),
                      journal.projectID == projectID, journal.transactionID == transactionID else {
                    throw PatchPackageError.restoreFailed
                }
                guard journal.status == .applied || journal.status == .prepared else { continue }
                items.append(PatchRecoveryItem(
                    receipt: PatchTransactionReceipt(id: transactionID, projectID: projectID, journalURL: journalURL),
                    createdAt: journal.createdAt,
                    targets: journal.records.map { $0.bundleID + "/" + $0.relativePath },
                    prepared: journal.status == .prepared
                ))
            }
        }
        return items.sorted { $0.createdAt > $1.createdAt }
    }
}
