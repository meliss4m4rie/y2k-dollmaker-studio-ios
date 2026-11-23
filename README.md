## iOS (Unsigned Build Artifact)

The GitHub Release includes an iOS build archive containing `App.app` (compiled via GitHub Actions on `macos-15` using `xcodebuild` against `ios/App/App.xcodeproj` with `CODE_SIGNING_ALLOWED=NO`).

- **Unsigned `.app` bundle:** This asset is an unsigned compiled iOS app bundle, not a signed `.ipa`. It will not install directly onto a standard iPhone without signing/packaging.
- **macOS / Xcode required to sign & install:** Building, signing, and deploying to an iPhone requires macOS and Xcode (with your own Apple Developer signing/provisioning setup).

### Building & Signing From Source on macOS
1. Clone the repository and sync web/Capacitor assets if needed:
   ```bash
   npm ci
   npx cap sync ios
