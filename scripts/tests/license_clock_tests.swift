var checks = 0
func require(_ condition: @autoclosure () -> Bool, _ label: String) {
    checks += 1
    if !condition() { fatalError("Regression failed: \(label)") }
}
let base = Date(timeIntervalSince1970: 1800000000)
for minutes in [60, 90, 120, 1440, 2880, 10080, 21600, 43200] {
    let expiry = base.addingTimeInterval(Double(minutes) * 60)
    let clock = InjectLicenseClock(expiresAt: expiry, now: base)
    require(clock.totalSeconds == minutes * 60, "duration \(minutes)m")
    require(clock.fraction(duration: Double(minutes) * 60) == 1, "initial fraction")
    let next = InjectLicenseClock(expiresAt: expiry, now: base.addingTimeInterval(1))
    require(next.totalSeconds == minutes * 60 - 1, "second-by-second \(minutes)m")
    let expired = InjectLicenseClock(expiresAt: expiry, now: expiry)
    require(expired.totalSeconds == 0 && expired.fraction(duration: Double(minutes) * 60) == 0, "expiry boundary")
}
let oneDay = InjectLicenseClock(expiresAt: base.addingTimeInterval(86400), now: base.addingTimeInterval(1))
require(oneDay.majorValue == "23" && oneDay.majorUnit == "horas", "one-day key displays hours, not zero days")
require(oneDay.remainingText == "23h 59m 59s restantes", "precise one-day countdown")
require(InjectLicenseClock.durationLabel(seconds: 86400) == "1 dia", "singular one-day duration")
require(InjectLicenseClock.durationLabel(seconds: 3600) == "1 hora", "singular one-hour duration")
let noExpiry = InjectLicenseClock(expiresAt: nil, now: base)
require(noExpiry.totalSeconds == nil && noExpiry.majorValue == "—" && noExpiry.majorUnit == "", "missing dates never invent days")
require(InjectLicenseClock(expiresAt: base.addingTimeInterval(0.001), now: base).totalSeconds == 1, "fractional final second")
let longKey = InjectLicenseClock(expiresAt: base.addingTimeInterval(2592000), now: base.addingTimeInterval(1))
require(longKey.days == 29 && longKey.hours == 23, "thirty-day countdown")

func fixture(minutes: Int) -> LicenseResponse {
    LicenseResponse(valid: true, code: "valid", message: "test", key: nil,
                    expiresAt: ISO8601DateFormatter().string(from: base.addingTimeInterval(Double(minutes) * 60)),
                    remainingUses: nil, deviceID: "unit-test-device", package: "unit-test-package",
                    durationDays: Int(ceil(Double(minutes) / 1440)), durationMinutes: minutes,
                    activatedAt: ISO8601DateFormatter().string(from: base))
}
var visibleMinutes: Int?
let observer = NotificationCenter.default.addObserver(forName: LicenseStore.profileDidChange, object: nil, queue: nil) { _ in
    visibleMinutes = LicenseStore.profileSnapshot?.durationMinutes
}
LicenseStore.save("UNIT-TEST-THIRTY-DAYS", response: fixture(minutes: 43200))
require(visibleMinutes == 43200, "mounted hidden home receives validated profile")
LicenseStore.save("UNIT-TEST-ONE-DAY", response: fixture(minutes: 1440))
require(visibleMinutes == 1440 && LicenseStore.profileSnapshot?.durationMinutes == 1440, "new one-day key replaces previous thirty-day profile")
LicenseStore.save("UNIT-TEST-DIFFERENT-KEY")
require(LicenseStore.profileSnapshot == nil, "cache cannot be reused for another key")
UserDefaults.standard.removeObject(forKey: "license-profile-key-fingerprint")
LicenseStore.save("UNIT-TEST-ONE-DAY")
require(LicenseStore.profileSnapshot == nil, "unbound legacy cache must be refreshed")
LicenseStore.save("UNIT-TEST-ONE-DAY", response: fixture(minutes: 1440))
require(visibleMinutes == 1440, "login repairs legacy snapshot")
NotificationCenter.default.removeObserver(observer)
print("\(checks) license countdown and validated-key synchronization checks passed.")
