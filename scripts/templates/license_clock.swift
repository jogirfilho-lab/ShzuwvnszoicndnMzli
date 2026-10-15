
struct InjectLicenseClock {
    let expiresAt: Date?
    let now: Date

    var totalSeconds: Int? {
        guard let expiresAt else { return nil }
        return Int(max(0, expiresAt.timeIntervalSince(now)).rounded(.up))
    }
    var days: Int { (totalSeconds ?? 0) / 86400 }
    var hours: Int { ((totalSeconds ?? 0) / 3600) % 24 }
    var minutes: Int { ((totalSeconds ?? 0) / 60) % 60 }
    var seconds: Int { (totalSeconds ?? 0) % 60 }
    var majorValue: String {
        guard let totalSeconds else { return "—" }
        if days > 0 { return String(days) }
        if hours > 0 { return String(hours) }
        if minutes > 0 { return String(minutes) }
        return String(totalSeconds)
    }
    var majorUnit: String {
        guard totalSeconds != nil else { return "" }
        if days > 0 { return days == 1 ? "dia" : "dias" }
        if hours > 0 { return hours == 1 ? "hora" : "horas" }
        if minutes > 0 { return minutes == 1 ? "minuto" : "minutos" }
        return totalSeconds == 1 ? "segundo" : "segundos"
    }
    var detail: String {
        guard totalSeconds != nil else { return "expiração não informada" }
        if days > 0 { return "\(hours)h \(minutes)m \(seconds)s restantes" }
        if hours > 0 { return "\(minutes)m \(seconds)s restantes" }
        return "\(seconds)s restantes"
    }
    var remainingText: String {
        guard totalSeconds != nil else { return "não configurada" }
        if days > 0 { return "\(days)d \(hours)h \(minutes)m \(seconds)s restantes" }
        if hours > 0 { return "\(hours)h \(minutes)m \(seconds)s restantes" }
        if minutes > 0 { return "\(minutes)m \(seconds)s restantes" }
        return "\(seconds)s restantes"
    }
    func fraction(duration: Double?) -> Double {
        guard let totalSeconds, let duration, duration > 0 else { return 0 }
        return min(1, max(0, Double(totalSeconds) / duration))
    }
    static func durationLabel(seconds: Double?) -> String {
        guard let seconds, seconds > 0 else { return "prazo não informado" }
        let minutes = Int(seconds / 60)
        if minutes % 1440 == 0 {
            let days = minutes / 1440
            return "\(days) \(days == 1 ? "dia" : "dias")"
        }
        if minutes % 60 == 0 {
            let hours = minutes / 60
            return "\(hours) \(hours == 1 ? "hora" : "horas")"
        }
        return "\(minutes) \(minutes == 1 ? "minuto" : "minutos")"
    }
}
