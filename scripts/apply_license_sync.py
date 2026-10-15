"""Fix hidden home initialization and prevent stale-key cache/response races."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
app = root / 'App.swift'
a = app.read_text()
a = 'import CryptoKit\n' + a
old = '''final class LicenseStore {
    private static let service'''
new = '''final class LicenseStore {
    // Preserve the validated session even if the signing tool denies a Keychain write.
    private static var activeSessionKey: String?
    private static let service'''
assert old in a
a = a.replace(old, new, 1)
old = '''    static var storedKey: String? {
        let query: [String: Any]'''
new = '''    static var storedKey: String? {
        if let activeSessionKey { return activeSessionKey }
        let query: [String: Any]'''
assert old in a
a = a.replace(old, new, 1)
old = '''    static func save(_ key: String) {
        let query: [String: Any]'''
new = '''    static func save(_ key: String) {
        activeSessionKey = key
        let query: [String: Any]'''
assert old in a
a = a.replace(old, new, 1)
start = a.index('extension LicenseStore {')
end = a.index('\nstruct LicenseProfileView: View {', start)
store = '''extension LicenseStore {
    static let profileDidChange = Notification.Name("LicenseProfileDidChange")
    private static let profileKey = "license-profile-snapshot"
    private static let profileFingerprintKey = "license-profile-key-fingerprint"

    private static func fingerprint(_ key: String) -> String {
        SHA256.hash(data: Data(key.trimmingCharacters(in: .whitespacesAndNewlines).uppercased().utf8))
            .map { String(format: "%02x", $0) }.joined()
    }

    static var profileSnapshot: LicenseProfileSnapshot? {
        guard let key = storedKey,
              UserDefaults.standard.string(forKey: profileFingerprintKey) == fingerprint(key),
              let data = UserDefaults.standard.data(forKey: profileKey) else { return nil }
        return try? JSONDecoder().decode(LicenseProfileSnapshot.self, from: data)
    }

    static func save(_ key: String, response: LicenseResponse) {
        save(key)
        let snapshot = LicenseProfileSnapshot(
            product: "inject chz",
            status: response.valid ? "VIP ATIVO" : "INATIVA",
            expiresAt: response.expiresAt,
            deviceID: response.deviceID,
            package: response.package,
            durationDays: response.durationDays,
            durationMinutes: response.durationMinutes,
            activatedAt: response.activatedAt
        )
        if let data = try? JSONEncoder().encode(snapshot) {
            UserDefaults.standard.set(data, forKey: profileKey)
            UserDefaults.standard.set(fingerprint(key), forKey: profileFingerprintKey)
            NotificationCenter.default.post(name: profileDidChange, object: nil)
        }
    }
}
'''
a = a[:start] + store + a[end:]
old = '''            let response = try await LicenseAPI.validate(key: key)
            guard response.valid else { return }
            LicenseStore.save(key, response: response)'''
new = '''            let response = try await LicenseAPI.validate(key: key)
            guard response.valid else { return }
            await MainActor.run {
                guard LicenseStore.storedKey == key else { return }
                LicenseStore.save(key, response: response)
                snapshot = LicenseStore.profileSnapshot
            }'''
assert old in a
a = a.replace(old, new, 1)
# Legacy profile participates in the same validated-key update event.
old = '''        .task {
            snapshot = LicenseStore.profileSnapshot
            await refreshSnapshot()
        }
'''
new = '''        .task {
            snapshot = LicenseStore.profileSnapshot
            await refreshSnapshot()
        }
        .onReceive(NotificationCenter.default.publisher(for: LicenseStore.profileDidChange)) { _ in
            snapshot = LicenseStore.profileSnapshot
        }
'''
assert old in a
a = a.replace(old, new, 1)
# If the user edited the key during validation, ignore the previous field value.
old = """                isLoading = false
                guard result.valid else { errorMessage = result.message; return }"""
new = """                isLoading = false
                guard key.trimmingCharacters(in: .whitespacesAndNewlines).uppercased() == candidate else { return }
                guard result.valid else { errorMessage = result.message; return }"""
assert old in a
a = a.replace(old, new, 1)
repo = Path(__file__).resolve().parent.parent
a += (repo / 'scripts/templates/license_clock.swift').read_text()
assert 'LicenseAPI.validate(key: candidate)' in a
assert 'profileFingerprintKey) == fingerprint(key)' in a
assert 'by: 1)' in a
app.write_text(a)
print('Validated key/profile notifications and stale-response guards installed.')
