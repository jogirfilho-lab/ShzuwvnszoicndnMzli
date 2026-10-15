"""Check the final generated sources, not an alternate implementation."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
s = (root / 'views/PatchProjectsView.swift').read_text()
c = (root / 'ContentView.swift').read_text()
nav = (root / 'helpers/AppTabNavigationState.swift').read_text()
assert '[AppSection.home, .patches, .textures]' in c
assert '[AppSection.home, .patches, .external, .textures]' not in c
assert '[.home, .patches, .textures].filter(isVisible)' in nav
assert 'ExternalPanelView(gameFilter: selectedGameID)' in s
assert 'base == gameFilter || base == "online-" + gameFilter' in s
assert 'gameFilter == nil || $0 != .textures' in s
assert 'PatchPackageDetailsView' in s and 'if !project.isPrivate' in s
assert 'rule.relativePath' in s and 'rule.replacementData.count' in s
assert 'Task.detached(priority: .userInitiated)' in s
assert '.transaction { $0.animation = nil }' in s
assert 'digest.caseInsensitiveCompare(sha256) == .orderedSame' in s
assert 'catalogKey == key' in s
assert 'cachedFile(named: patch.fileName)' not in s[s.index('static func resolve(patch: PreloadedPatch)'):s.index('\nimport SwiftUI', s.index('static func resolve(patch: PreloadedPatch)'))]
assert 'Recurso pré-carregado do Free Fire.' not in s
# Preserve the real receipt and existing timed restoration, do not fake success.
assert 'DevicePatchService.apply(project: decoded.project)' in s
assert 'DevicePatchService.restore(receipt: receipt)' in s
assert '5_000_000_000' in s
print('Merged navigation, file details, privacy and verified-cache invariants passed.')
