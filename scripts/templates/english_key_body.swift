    var body: some View {
        GeometryReader { geometry in
            ZStack {
                Color.black.ignoresSafeArea()
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 0) {
                        Color.clear.frame(height: max(28, geometry.size.height * 0.09))
                        ExternalCheatsKeyHeader()
                            .aspectRatio(800.0 / 450.0, contentMode: .fit)
                            .frame(maxWidth: .infinity)
                        VStack(alignment: .leading, spacing: 13) {
                            Text("ACCESS KEY")
                                .font(.system(size: 12, weight: .medium))
                                .tracking(2.5)
                                .foregroundStyle(Color.gray)
                            SecureField("", text: $key)
                                .accessibilityLabel("Access key")
                                .textInputAutocapitalization(.characters)
                                .autocorrectionDisabled()
                                .submitLabel(.go)
                                .onSubmit {
                                    if !isLoading && !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { validate() }
                                }
                                .padding(.horizontal, 16)
                                .frame(height: 54)
                                .background(Color(white: 0.095), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                                .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.white.opacity(0.1), lineWidth: 1))
                                .foregroundStyle(.white)
                        }.padding(.top, 45)
                        Group {
                            if let errorMessage {
                                Text(englishUIMessage(errorMessage))
                                    .font(.system(size: 13, weight: .medium))
                                    .foregroundStyle(.white)
                                    .multilineTextAlignment(.center)
                            } else { Color.clear.frame(height: 1) }
                        }.frame(minHeight: 34).padding(.horizontal, 4).padding(.vertical, 9)
                        Button(action: validate) {
                            Group {
                                if isLoading { ProgressView().tint(.black) }
                                else { Text("SIGN IN").font(.system(size: 17, weight: .bold)).tracking(2.5) }
                            }
                            .frame(maxWidth: .infinity).frame(height: 56)
                            .foregroundStyle(.black)
                            .background(Color(white: 0.92), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                        }
                        .buttonStyle(.plain)
                        .disabled(isLoading || key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        Spacer(minLength: 36)
                    }
                    .frame(maxWidth: 520)
                    .padding(.horizontal, 30)
                    .frame(minHeight: geometry.size.height)
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .preferredColorScheme(.dark)
        .task { await validateStoredKey() }
    }

