# expo: EAS — Build, Submit, Update, credentials

Verified against SDK 58 docs (`docs.expo.dev/build/introduction.md`, `docs.expo.dev/eas-update/introduction.md`; append `.md`).

## Profiles and commands
- `eas.json` profiles: `development` (dev client, internal), `preview` (internal distribution, release mode), `production` (store).
- `eas build -p ios|android --profile <p>` → `eas submit`. Queue builds from CI (EAS Workflows or GitHub Actions).
- Credentials are managed by EAS. Use `appVersionSource: remote` with `autoIncrement` for build numbers so every source of truth agrees.

## EAS Update (OTA)
- Ships JS and assets only, to a matching `runtimeVersion` — set via `policy: appVersion` or `fingerprint`. Any native change requires a new build, never an update.
- Channels per environment (development/preview/production); branch-based workflow for test → production.
- Roll out gradually, keep a rollback update ready, monitor update downloads with Expo Observe.

## Expo Observe
See `observe.md` in this folder.

## Pitfalls
Hand-editing native folders under a managed project; shipping an OTA that depends on new native code (crash on mismatched runtime); committing credentials to the repo; one shared runtimeVersion policy across app versions.
