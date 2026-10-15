"""Restyle LicenseLoginView only; retain API, key storage, and success callback."""
from pathlib import Path
import sys

app = Path(sys.argv[1]) / 'App.swift'
text = app.read_text()
view = text.index('struct LicenseLoginView: View {')
start = text.index('    var body: some View {', view)
end = text.index('    private func validateStoredKey()', start)
original_logic = text[end:]
body = '''    var body: some View {
        GeometryReader { geometry in
            ZStack {
                LinearGradient(
                    colors: [Color.black, Color.black, Color(red: 0.018, green: 0.021, blue: 0.026)],
                    startPoint: .top,
                    endPoint: .bottom
                ).ignoresSafeArea()
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        Color.clear.frame(height: max(64, geometry.size.height * 0.24))
                        Image(systemName: "shield.lefthalf.filled")
                            .font(.system(size: 50, weight: .semibold))
                            .foregroundStyle(Color(red: 0.93, green: 0.015, blue: 0.035))
                            .accessibilityHidden(true)
                        Text("EXTERNAL CHZ")
                            .font(.system(size: 25, weight: .bold))
                            .foregroundStyle(Color.white)
                            .padding(.top, 24)
                            .minimumScaleFactor(0.8)
                            .lineLimit(1)
                        VStack(alignment: .leading, spacing: 9) {
                            Text("CHAVE DE ACESSO")
                                .font(.system(size: 12, weight: .bold))
                                .foregroundStyle(Color.gray)
                            SecureField("", text: $key)
                                .accessibilityLabel("Chave de acesso")
                                .textInputAutocapitalization(.characters)
                                .autocorrectionDisabled()
                                .submitLabel(.go)
                                .onSubmit {
                                    if !isLoading && !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { validate() }
                                }
                                .padding(.horizontal, 16)
                                .frame(height: 52)
                                .background(Color(red: 0.13, green: 0.13, blue: 0.14), in: RoundedRectangle(cornerRadius: 15, style: .continuous))
                                .foregroundStyle(Color.white)
                        }.padding(.top, 64)
                        Group {
                            if let errorMessage {
                                Text(errorMessage)
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundStyle(Color.red)
                                    .multilineTextAlignment(.center)
                            } else {
                                Color.clear.frame(height: 1)
                            }
                        }.frame(minHeight: 60).padding(.horizontal, 4)
                        Button(action: validate) {
                            Group {
                                if isLoading { ProgressView().tint(.white) }
                                else { Text("ENTRAR").font(.system(size: 17, weight: .bold)) }
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                            .foregroundStyle(Color.white)
                            .background(Color(red: 0.93, green: 0.015, blue: 0.035), in: RoundedRectangle(cornerRadius: 15, style: .continuous))
                        }
                        .buttonStyle(.plain)
                        .disabled(isLoading || key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        Spacer(minLength: 36)
                    }
                    .frame(maxWidth: 520)
                    .frame(minHeight: geometry.size.height)
                    .padding(.horizontal, 28)
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .preferredColorScheme(.dark)
        .task { await validateStoredKey() }
    }

'''
text = text[:start] + body + text[end:]
assert text[text.index('    private func validateStoredKey()', view):] == original_logic
assert 'LicenseAPI.validate(key: candidate)' in text
assert 'LicenseStore.save(candidate, response: result)' in text
assert 'onSuccess()' in text
app.write_text(text)
print('Key screen restyled; authentication and storage logic unchanged.')
