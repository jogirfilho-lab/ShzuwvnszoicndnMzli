
private struct ExternalCheatsKeyHeader: UIViewRepresentable {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private static let gifData = Data(base64Encoded: "@@HEADER_GIF_BASE64@@")!
    private static let decoded: (frames: [UIImage], duration: TimeInterval) = {
        guard let source = CGImageSourceCreateWithData(gifData as CFData, nil) else { return ([], 0) }
        var frames: [UIImage] = []
        var duration: TimeInterval = 0
        for index in 0..<CGImageSourceGetCount(source) {
            guard let image = CGImageSourceCreateImageAtIndex(source, index, nil) else { continue }
            frames.append(UIImage(cgImage: image))
            let properties = CGImageSourceCopyPropertiesAtIndex(source, index, nil) as? [CFString: Any]
            let gif = properties?[kCGImagePropertyGIFDictionary] as? [CFString: Any]
            let delay = (gif?[kCGImagePropertyGIFUnclampedDelayTime] as? NSNumber)?.doubleValue
                ?? (gif?[kCGImagePropertyGIFDelayTime] as? NSNumber)?.doubleValue ?? 0.1
            duration += max(delay, 0.02)
        }
        return (frames, duration)
    }()
    func makeUIView(context: Context) -> UIView {
        let container = UIView()
        container.backgroundColor = .clear
        container.isAccessibilityElement = true
        container.accessibilityLabel = "EXTERNAL CHEATS"
        let image = UIImageView()
        image.tag = 531
        image.contentMode = .scaleAspectFit
        image.backgroundColor = .clear
        image.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(image)
        NSLayoutConstraint.activate([
            image.leadingAnchor.constraint(equalTo: container.leadingAnchor),
            image.trailingAnchor.constraint(equalTo: container.trailingAnchor),
            image.topAnchor.constraint(equalTo: container.topAnchor),
            image.bottomAnchor.constraint(equalTo: container.bottomAnchor)
        ])
        return container
    }
    func updateUIView(_ uiView: UIView, context: Context) {
        guard let image = uiView.viewWithTag(531) as? UIImageView else { return }
        image.image = Self.decoded.frames.first
        if reduceMotion {
            image.stopAnimating()
            image.animationImages = nil
        } else if !image.isAnimating {
            image.animationImages = Self.decoded.frames
            image.animationDuration = Self.decoded.duration
            image.animationRepeatCount = 0
            image.startAnimating()
        }
    }
    static func dismantleUIView(_ uiView: UIView, coordinator: ()) {
        (uiView.viewWithTag(531) as? UIImageView)?.stopAnimating()
    }
}
