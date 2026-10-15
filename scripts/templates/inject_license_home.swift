
struct InjectLicenseHomeView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.scenePhase) private var scenePhase
    @State private var snapshot: LicenseProfileSnapshot?
    @State private var lastCheck: Date?
    @State private var networkUnavailable = false
    @State private var validationDenied = false
    private let red = Color(red: 0.96, green: 0.12, blue: 0.20)
    private let border = Color(red: 0.58, green: 0.035, blue: 0.09)

    private func parseDate(_ raw: String?) -> Date? {
        guard let raw else { return nil }
        let iso = ISO8601DateFormatter()
        iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = iso.date(from: raw) { return date }
        iso.formatOptions = [.withInternetDateTime]
        return iso.date(from: raw)
    }
    private var endDate: Date? { parseDate(snapshot?.expiresAt) }
    private var durationSeconds: Double? {
        if let minutes = snapshot?.durationMinutes, minutes > 0 { return Double(minutes) * 60 }
        if let days = snapshot?.durationDays, days > 0 { return Double(days) * 86400 }
        if let start = parseDate(snapshot?.activatedAt), let end = endDate, end > start { return end.timeIntervalSince(start) }
        return nil
    }
    private var durationLabel: String {
        InjectLicenseClock.durationLabel(seconds: durationSeconds)
    }
    private var deviceID: String {
        let id = snapshot?.deviceID ?? UIDevice.current.identifierForVendor?.uuidString ?? "indisponível"
        return id.count > 22 ? String(id.prefix(22)) + "…" : id
    }
    private var expiration: String {
        guard let date = endDate else { return "não configurada" }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "pt_BR")
        formatter.dateFormat = "dd/MM/yyyy, HH:mm"
        return formatter.string(from: date)
    }
    private func active(at date: Date) -> Bool {
        guard let snapshot, !validationDenied else { return false }
        if let endDate, endDate <= date { return false }
        return snapshot.status.uppercased().contains("ATIVO")
    }
    private func remaining(at date: Date) -> String {
        let clock = InjectLicenseClock(expiresAt: endDate, now: date)
        guard clock.totalSeconds != nil else { return "não configurada" }
        return "\(durationLabel) · \(clock.remainingText)"
    }

    var body: some View {
        ZStack {
            LinearGradient(colors: [Color(red: 0.105, green: 0.006, blue: 0.020), Color.black, Color.black], startPoint: .topTrailing, endPoint: .bottomLeading)
                .ignoresSafeArea()
            ScrollView(.vertical, showsIndicators: false) {
                VStack(alignment: .leading, spacing: 18) {
                    Text("Licença")
                        .font(.system(size: 16, weight: .semibold)).foregroundStyle(.white)
                        .frame(maxWidth: .infinity).padding(.top, 8)
                    HStack(spacing: 16) {
                        Image("InjectCHZLogo").resizable().scaledToFit().frame(width: 130, height: 86)
                            .accessibilityLabel("inject chz")
                        Spacer()
                    }.padding(.bottom, 5)
                    TimelineView(.periodic(from: .now, by: 1)) { clock in
                        VStack(alignment: .leading, spacing: 18) {
                            timeCard(at: clock.date)
                            sectionLabel("INFORMAÇÕES DA LICENÇA")
                            card {
                                row("Produto", value: "inject chz")
                                divider
                                row("Status da Key", value: active(at: clock.date) ? "ϟ  VIP ATIVO" : (snapshot == nil ? "INDISPONÍVEL" : "INATIVA"), highlighted: true)
                                divider
                                row("Tempo da Key", value: remaining(at: clock.date))
                                divider
                                row("ID do Dispositivo", value: deviceID, subdued: true)
                            }
                        }
                    }
                    sectionLabel("DISPOSITIVO & COMPATIBILIDADE")
                    card {
                        row("Modelo", value: AppInfo.displayMachineName)
                        divider
                        row("Versão iOS", value: "\(AppInfo.osVersion) (\(AppInfo.osBuild))")
                    }
                    sectionLabel("SEGURANÇA & ANTICRACK")
                    card {
                        row("Proteção Anti-Debugging", value: "⚠  NÃO VERIFICADA", highlighted: true)
                        divider
                        row("Integridade do painel", value: signaturePresent ? "ASSINATURA PRESENTE" : "NÃO VERIFICADA", highlighted: true)
                    }
                    HStack(spacing: 5) {
                        Image(systemName: "shield.fill").font(.system(size: 9))
                        Text(checkFooter).font(.system(size: 9))
                    }.foregroundStyle(Color.white.opacity(0.42)).frame(maxWidth: .infinity).padding(.vertical, 6)
                }.padding(.horizontal, 16).padding(.bottom, 12)
            }
        }
        .preferredColorScheme(.dark)
        .navigationBarHidden(true)
        .task {
            snapshot = LicenseStore.profileSnapshot
            await refreshLicense()
        }
        .onReceive(NotificationCenter.default.publisher(for: LicenseStore.profileDidChange)) { _ in
            snapshot = LicenseStore.profileSnapshot
            validationDenied = false
            networkUnavailable = false
            lastCheck = Date()
        }
        .onChange(of: scenePhase) { phase in
            if phase == .active { Task { await refreshLicense() } }
        }
        .refreshable { await refreshLicense() }
    }

    private var signaturePresent: Bool {
        FileManager.default.fileExists(atPath: Bundle.main.bundlePath + "/_CodeSignature/CodeResources")
    }
    private var checkFooter: String {
        if networkUnavailable { return "inject chz · dados locais · sem conexão com a API" }
        if let lastCheck { return "inject chz · consulta à API às \(lastCheck.formatted(date: .omitted, time: .shortened))" }
        return "inject chz · aguardando consulta à API"
    }
    private func refreshLicense() async {
        guard let key = LicenseStore.storedKey else { return }
        do {
            let response = try await LicenseAPI.validate(key: key)
            await MainActor.run {
                // The hidden home may have requested the previously stored key before login.
                // Never let that late response replace a newly validated key/profile.
                guard LicenseStore.storedKey == key else { return }
                lastCheck = Date()
                networkUnavailable = false
                validationDenied = !response.valid
                if response.valid {
                    LicenseStore.save(key, response: response)
                }
                snapshot = LicenseStore.profileSnapshot
            }
        } catch {
            await MainActor.run {
                guard LicenseStore.storedKey == key else { return }
                networkUnavailable = true
            }
        }
    }
    private func sectionLabel(_ text: String) -> some View {
        Text(text).font(.system(size: 10, weight: .bold)).tracking(1.4)
            .foregroundStyle(Color.white.opacity(0.9)).padding(.top, 2).padding(.horizontal, 2)
    }
    private var divider: some View {
        Rectangle().fill(Color.white.opacity(0.07)).frame(height: 0.5).padding(.horizontal, 14)
    }
    private func row(_ title: String, value: String, highlighted: Bool = false, subdued: Bool = false) -> some View {
        HStack(spacing: 10) {
            Text(title).font(.system(size: 12)).foregroundStyle(.white)
            Spacer(minLength: 8)
            Text(value).font(.system(size: 11, weight: highlighted ? .bold : .medium))
                .foregroundStyle(highlighted ? red : Color.white.opacity(subdued ? 0.40 : 0.72))
                .multilineTextAlignment(.trailing).lineLimit(2).minimumScaleFactor(0.8)
        }.padding(.horizontal, 14).padding(.vertical, 18)
    }
    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        VStack(spacing: 0, content: content)
            .frame(maxWidth: .infinity)
            .background(Color(red: 0.075, green: 0.030, blue: 0.039), in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(border, lineWidth: 1))
            .shadow(color: red.opacity(0.12), radius: 9, y: 3)
    }
    private func timeCard(at now: Date) -> some View {
        let clock = InjectLicenseClock(expiresAt: endDate, now: now)
        let ratio = clock.fraction(duration: durationSeconds)
        return VStack(alignment: .leading, spacing: 9) {
            HStack {
                Text("TEMPO DE ACESSO").font(.system(size: 9, weight: .medium)).tracking(1.8).foregroundStyle(.gray)
                Spacer()
                Text(active(at: now) ? "ATIVO" : "INATIVO").font(.system(size: 8, weight: .bold)).tracking(0.9)
                    .foregroundStyle(red).padding(.horizontal, 13).padding(.vertical, 5)
                    .background(red.opacity(0.07), in: Capsule())
                    .overlay(Capsule().stroke(border.opacity(0.8), lineWidth: 0.5))
            }
            HStack(alignment: .firstTextBaseline, spacing: 7) {
                Text(clock.majorValue).font(.system(size: 42, weight: .bold)).foregroundStyle(.white)
                Text(clock.majorUnit).font(.system(size: 15, weight: .semibold)).foregroundStyle(.white)
            }
            Text(clock.detail)
                .font(.system(size: 10)).foregroundStyle(.gray).padding(.leading, 47)
            GeometryReader { area in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.white.opacity(0.05))
                    Capsule().fill(LinearGradient(colors: [Color(red: 0.68, green: 0.025, blue: 0.09), red], startPoint: .leading, endPoint: .trailing))
                        .frame(width: area.size.width * CGFloat(ratio))
                }
            }.frame(height: 4)
            HStack {
                Text(endDate == nil ? "aguardando ativação" : "Expira em \(expiration)")
                Spacer()
            }.font(.system(size: 8)).foregroundStyle(.gray)
        }.padding(14).background(Color(red: 0.068, green: 0.029, blue: 0.035), in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(border, lineWidth: 1))
            .shadow(color: red.opacity(0.10), radius: 8)
    }
}
