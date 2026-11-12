# Webconfig dependency consolidation

Reviewed 2026-11-07, with bench follow-up and final local checks on 2026-11-12. This review covers the eleven open webconfig Dependabot PRs **#51–#60 and #62** against upstream commit `8c48cfe422bae50b96b04b9c8de813d434e0bd54`. The consolidated lockfile includes their compatible updates and the required configuration/CSS migrations. **TypeScript 7 from #52 is deferred:** the typed-lint toolchain supports TypeScript 6, so this branch uses 6.0.3.

The review used PR manifests, upstream migration guides and release notes, published npm peer/engine metadata, and local checks. Package ranges can resolve newer versions than the original PRs; the table records the actual old and new lockfiles. User-reported physical output validation and the remaining hardware checks are recorded below.

## Changes represented by the lockfile

| PR                                                      | Package                       | Previous lock | Consolidated lock                  |
| ------------------------------------------------------- | ----------------------------- | ------------- | ---------------------------------- |
| [#51](https://github.com/Gugic/fanadapter/pull/51)      | `@radix-ui/react-dialog`      | 1.1.15        | 1.3.1                              |
| #51                                                     | `@radix-ui/react-label`       | 2.1.8         | 2.1.17                             |
| #51                                                     | `@radix-ui/react-separator`   | 1.1.8         | 1.2.0                              |
| #51                                                     | `@radix-ui/react-slider`      | 1.3.6         | 1.6.1                              |
| #51                                                     | `@radix-ui/react-slot`        | 1.2.4         | 1.5.0                              |
| #51                                                     | `@radix-ui/react-switch`      | 1.2.6         | 1.4.1                              |
| #51                                                     | `@radix-ui/react-tabs`        | 1.1.13        | 1.2.1                              |
| [#52](https://github.com/Gugic/fanadapter/pull/52)      | `@eslint/js`                  | 9.39.4        | 10.0.1                             |
| #52                                                     | `eslint`                      | 10.8.0        | 10.14.0                            |
| #52                                                     | `eslint-plugin-react-refresh` | 0.4.26        | 0.5.7                              |
| #52                                                     | `typescript`                  | 5.8.3         | **6.0.3; proposed 7.0.2 deferred** |
| #52                                                     | `typescript-eslint`           | 8.65.0        | 8.72.1                             |
| [#53](https://github.com/Gugic/fanadapter/pull/53)      | `@vitejs/plugin-react`        | 4.7.0         | 6.2.1                              |
| #53                                                     | `vite`                        | 6.4.3         | 8.3.6                              |
| #53, [#62](https://github.com/Gugic/fanadapter/pull/62) | `vitest`                      | 4.1.11        | 5.1.0                              |
| #62                                                     | `@vitest/mocker` (transitive) | 4.1.11        | 5.1.0                              |
| [#54](https://github.com/Gugic/fanadapter/pull/54)      | `tailwindcss`                 | 3.4.19        | 4.3.5                              |
| [#55](https://github.com/Gugic/fanadapter/pull/55)      | `tailwind-merge`              | 3.6.0         | 3.7.0                              |
| [#56](https://github.com/Gugic/fanadapter/pull/56)      | `postcss`                     | 8.5.23        | 8.5.32                             |
| [#57](https://github.com/Gugic/fanadapter/pull/57)      | `@types/node`                 | 25.9.1        | 26.6.6                             |
| [#58](https://github.com/Gugic/fanadapter/pull/58)      | `lucide-react`                | 1.16.0        | 1.70.0                             |
| [#59](https://github.com/Gugic/fanadapter/pull/59)      | `autoprefixer`                | 10.5.0        | 10.6.2                             |
| [#60](https://github.com/Gugic/fanadapter/pull/60)      | `react`                       | 19.2.6        | 19.3.1                             |
| #60, companion update                                   | `react-dom`                   | 19.2.6        | 19.3.1                             |
| #60                                                     | `@types/react`                | 19.2.15       | 19.3.0                             |
| #60, companion update                                   | `@types/react-dom`            | 19.2.3        | 19.3.0                             |

Additional direct development dependencies are `@tailwindcss/postcss` 4.3.5 for Tailwind 4, `@playwright/test` 1.65.0 for production-browser regression checks, and `audit-ci` 7.1.0. The latter replaces the existing untracked `npx audit-ci@7.1.0` download with a lockfile-controlled installation. A targeted `npm update zod` also updates that transitive package from 4.4.3 to 4.6.7 to remove a high advisory.

GitHub Actions dependency PRs #46–#50 are outside this consolidation. Changing the Node version used by webconfig workflows is necessary for the new test toolchain and does not adopt those action-version upgrades.

## Build and type compatibility

The local reference environment is **Node 26.12.0 / npm 11.20.0**. Node 26 is LTS and matches the Node 26 declarations; Node 20 has reached end of life. Vitest 5 requires Node `^22.12.0 || ^24.0.0 || >=26.0.0`, so the previous CI Node 20 is incompatible. The selected runtime also satisfies ESLint, Vite, and the React plugin. [Node release schedule](https://github.com/nodejs/Release/blob/main/schedule.json), [Vitest migration guide](https://vitest.dev/guide/migration/).

`typescript-eslint@8.72.1` declares TypeScript `>=4.8.4 <6.1.0`. Replacing its `typescript` dependency directly with TypeScript 7 would break the supported peer relationship and typed linting. This change uses `~6.0.3` without bypassing peer validation. Revisit the deferred portion of #52 when the lint stack supports TypeScript 7, or separately validate the dual-version approach assessed below. [Supported dependency versions](https://typescript-eslint.io/users/dependency-versions/), [versioned package metadata](https://github.com/typescript-eslint/typescript-eslint/blob/v8.72.1/packages/typescript-eslint/package.json).

TypeScript 6 requires small configuration changes here: remove deprecated `baseUrl` while retaining relative `paths`, and explicitly load Node types in the Vite configuration project. Its newer DOM declarations also exposed an inaccurate local WebSerial type: `Uint8Array` permitted shared buffers, while `TextDecoderStream` expects ordinary buffers. The serial stream declarations now specify `Uint8Array<ArrayBuffer>`; runtime transport logic is unchanged. [TypeScript 6 release and migration notes](https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/).

ESLint was already version 10, but its `@eslint/js` recommended preset now catches up. The newly enabled `no-unassigned-vars`, `no-useless-assignment`, and `preserve-caught-error` rules pass without disabling them. React Refresh 0.5 uses the preferred named export and `.plugin` registration in the existing flat ESM configuration. No custom HOC option needs migrating. [ESLint 10 guide](https://eslint.org/docs/latest/use/migrate-to-10.0.0), [React Refresh 0.5 notes](https://github.com/ArnaudBarre/eslint-plugin-react-refresh/releases/tag/v0.5.0).

Vite 7 and 8 change browser targets and replace the Rollup/esbuild build pipeline with Rolldown/Oxc and Lightning CSS. This app has no custom bundler hooks, SSR, Sass, decorator, or optimizer configuration to migrate. React plugin 6 removes Babel-specific features, but this project uses plain `react()` without Babel plugins. Production-browser checks are needed because compiler/minifier changes can affect behavior despite a successful build. [Vite 7 migration](https://v7.vite.dev/guide/migration), [Vite 8 migration](https://vite.dev/guide/migration), [React plugin 6 release](https://github.com/vitejs/vite-plugin-react/releases/tag/plugin-react@6.0.0).

Vitest 5 clears mock history before each test. Existing tests create mocks per test and restore globals/timers; they do not depend on accumulated calls or use the affected project, benchmark, or browser-mode APIs. All 26 existing tests passed after upgrading. The resolved Vite 8.3.6, React plugin 6.2.0–6.2.1, and Vitest 5.1.0 release notes were also reviewed; no further project configuration migration was identified. [Vite 8.3.6](https://github.com/vitejs/vite/releases/tag/v8.3.6), [plugin 6.2.0](https://github.com/vitejs/vite-plugin-react/releases/tag/plugin-react@6.2.0), [plugin 6.2.1](https://github.com/vitejs/vite-plugin-react/releases/tag/plugin-react@6.2.1), [Vitest 5.1.0](https://github.com/vitest-dev/vitest/releases/tag/v5.1.0).

## UI and CSS compatibility

Tailwind 4 is a substantive migration. Its PostCSS plugin moves to `@tailwindcss/postcss`, CSS uses `@import`, and the existing JavaScript theme needs explicit `@config`. This migration preserves semantic HSL colors, class-based dark mode, and the animation plugin. Browser comparison caught lost spacing above controls because v4 changes `space-y` margins; six affected label locations now use explicit block layout and the original 24px line box. It reconstructs the previous container behavior in CSS, preserves the existing emerald color, renames shadow/outline/backdrop utilities where their meaning changed, and preserves enabled-button pointer cursors. The project's custom radius names stay unchanged because applying stock-radius renames would change their values. [Tailwind upgrade guide](https://tailwindcss.com/docs/upgrade-guide).

The supported device UI now requires **desktop Chromium 111+**. Tailwind's modern CSS and Vite's default output both contribute to that floor. Browser checks should cover responsive spacing, dialogs, focus rings, semantic colors, switch movement, and range-slider appearance. Shadcn metadata uses the Tailwind 4 empty config field while CSS explicitly loads the retained JavaScript theme. [Shadcn configuration reference](https://ui.shadcn.com/docs/components-json#tailwindconfig).

Tailwind 4.3.4–4.3.5 include source detection, parsing, PostCSS URL rewriting, and plugin fixes; no additional migration was needed for the app's usage. `tailwind-merge` 3.7 supports Tailwind 4 and needs no customization change. The previous Tailwind 3 / merge 3 pairing was outside merge's documented Tailwind version range. [Tailwind 4.3.4](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.4), [Tailwind 4.3.5](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5), [merge 3.7](https://github.com/dcastil/tailwind-merge/releases/tag/tailwind-merge%403.7.0), [merge compatibility](https://github.com/dcastil/tailwind-merge/blob/main/README.md).

Radix's updated peers accept React 19. The reviewed component APIs remain available, but several behavioral fixes deserve explicit regression coverage:

- Dialog focus, scroll locking, Escape, and focus restoration. [Dialog changelog](https://github.com/radix-ui/primitives/blob/main/packages/react/dialog/CHANGELOG.md).
- Slider keyboard stepping, crossing thumbs, and `onValueCommit`, which the app uses for calibration. [Slider changelog](https://github.com/radix-ui/primitives/blob/main/packages/react/slider/CHANGELOG.md).
- Tabs now move focus before state changes, affecting numeric fields that commit on blur. [Tabs changelog](https://github.com/radix-ui/primitives/blob/main/packages/react/tabs/CHANGELOG.md).
- Switch checked/disabled behavior and composed refs in `asChild` buttons. [Switch changelog](https://github.com/radix-ui/primitives/blob/main/packages/react/switch/CHANGELOG.md), [Slot changelog](https://github.com/radix-ui/primitives/blob/main/packages/react/slot/CHANGELOG.md).

React and React DOM resolve to the same 19.3.1 version, with both type packages on 19.3. The new transition/fragment APIs are unused, and no required source migration was found. Connection subscriptions and cleanup should still be checked during development refreshes. The 19.3.1 fixes concern Server Components transport, which this static SPA does not use. [React 19.3 release](https://react.dev/blog/2026/09/09/react-19-3), [19.3.1 notes](https://github.com/facebook/react/releases/tag/v19.3.1).

Lucide's renderer and release notes through the resolved 1.70.0 were reviewed. Version 1.68 renames some warning icons, so the existing `AlertCircle` alias was checked explicitly. All 18 icon exports used by the app/dialog rendered as SVG with the expected view box and supplied classes. This establishes API/rendering compatibility, not identical icon geometry. [Renderer at 1.55](https://github.com/lucide-icons/lucide/blob/1.55.0/packages/lucide-react/src/Icon.ts), [1.68 notes](https://github.com/lucide-icons/lucide/releases/tag/1.68.0), [1.70 notes](https://github.com/lucide-icons/lucide/releases/tag/1.70.0).

PostCSS 8.5.24–8.5.32 and Autoprefixer 10.5.1–10.6.2 contain parser, source-map, prefix, and type fixes that require no configuration changes here. Autoprefixer remains installed, although Tailwind 4 handles prefixing itself; removing it can be a separate simplification. [PostCSS releases](https://github.com/postcss/postcss/releases), [Autoprefixer releases](https://github.com/postcss/autoprefixer/releases).

## Security review

PR #62's Vitest 4.1.12 fix is included in the selected Vitest 5 line. Upstream [backport #11580](https://github.com/vitest-dev/vitest/pull/11580) identifies [original #11377](https://github.com/vitest-dev/vitest/pull/11377), merged as `15cc006aa9f8683dc5f7e895d011fa7dc751ce35` and released in [5.0.3](https://github.com/vitest-dev/vitest/releases/tag/v5.0.3). Comparing that commit to 5.0.5 returned `ahead`, 121 commits ahead and zero behind. The lockfile's Vitest and mocker 5.1.0 continue that release line; no vulnerable 4.x mocker remains.

The Zod transitive update to 4.6.7 exceeds the patched floor 4.6.6 for [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5). Tailwind 4 removes the dependency path behind the old braces exception, so `audit-ci.jsonc` no longer has an allowlist. High and critical advisories still fail the gate.

The latest audit still reports **10 moderate affected-package entries**, propagated through ESLint/typescript-eslint from `minimatch` 10.2.6 and [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249). This is one underlying advisory, not ten independent vulnerabilities. The upstream patch is 11.0.1, outside those consumers' supported ranges. Keep this visible: do not force an unreviewed major override or use the audit tool's suggested old lint-stack downgrades. Revisit when compatible upstream releases consume the fix. A passing high/critical gate does **not** mean a clean audit.

## Validation record and remaining device checks

Final local checks ran on macOS arm64 and Docker Linux arm64 with Node 26.12.0 / npm 11.20.0. The GitHub Actions workflow uses the same Node pin and check command. The records below describe local validation; remote check status is reported on the pull request.

| Check                                             | Recorded status                                                                                                                                                                                                                                                        |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Clean dependency installation and peer resolution | Passed: `npm ci` on host and in Docker; `npm ls --depth=0` has no invalid peers                                                                                                                                                                                        |
| Formatting, ESLint, TypeScript, production build  | Passed through `npm run check` on host and in Docker                                                                                                                                                                                                                   |
| Existing unit tests                               | Passed: 4 files, 26 tests under Vitest 5.1.0                                                                                                                                                                                                                           |
| Playwright production-browser suite               | Passed: 4 scenarios under `/fanadapter/`, repeated under custom `/review-preview/`; default build restored                                                                                                                                                             |
| Browser checks                                    | Production asset loads, light/dark colors, dialog open/focus/Escape/reopen, serial session, tab-switch blur commits, both slider thumbs, visible switch movement, label spacing, save/disconnect, unsupported browser                                                  |
| Baseline/current UI comparison                    | Compared screenshots and computed geometry: disconnected at 375/640/768/1024/1280px; dialog and connected Devices/Mappings/Outputs/Logs at 1280px. No remaining non-label geometry differences in the compared elements; labels intentionally use explicit block boxes |
| App/dialog icon rendering                         | Passed: all 18 imported icon exports                                                                                                                                                                                                                                   |
| Docker development/preview                        | Passed HTTP checks for dev HTML/Vite client/transformed TSX and production HTML/JS/CSS; concurrent services, host file ownership, configurable ports, stop/reset verified                                                                                              |
| Full dependency audit                             | Zero high/critical; 10 moderate affected-package entries from one advisory                                                                                                                                                                                             |
| Production dependency audit                       | `npm audit --omit=dev`: zero reported vulnerabilities                                                                                                                                                                                                                  |
| Whitespace and manifest/lock agreement            | Passed                                                                                                                                                                                                                                                                 |
| Physical WebSerial/WebUSB session                 | User-reported output, persistence, connection recovery, preview and development-refresh checks passed; USB pedal mapping partially passed with a throttle issue also reproduced on published main. See physical validation below                                       |

The default production bundle grows from 356.60 kB JS / 24.56 kB CSS to 392.63 kB JS / 34.25 kB CSS. Gzip sizes grow from 109.85 / 5.33 kB to 121.83 / 6.78 kB respectively (Vite build output). This is an observed cost of the combined toolchain/UI update, not a performance benchmark. Browser execution used Playwright 1.65.0's bundled Chromium; the documented minimum Chromium 111 was not separately tested.

Two existing behaviors reproduced in both the baseline and updated app deserve follow-up:

- The externally controlled firmware dialog leaves focus on the document body after Escape; it has no Radix trigger to restore focus to. Tests cover focus inside the dialog, closing and reopening, without claiming focus restoration is fixed.
- Crossing one deadzone thumb past the other can produce two stale full-binding writes: starting at `[16384, 32768]` and crossing the low thumb past the high one ended at `[16384, 47488]` rather than `[32768, 47488]`. `RangeSliderField` assumes only one endpoint changes per commit. Normal independent endpoint edits pass, but the existing crossing behavior needs its own fix; the dependency update does not establish correctness for that case.

The browser suite exercises production assets under the Pages subfolder, UI styling, firmware-dialog behavior, connection state, tab/blur commits, switches, range sliders, save/disconnect, and unsupported-browser handling. Its simulated serial responses cannot validate browser permission prompts, real USB transfers, firmware timing, or wheelbase outputs.

## TypeScript 7 follow-up assessment — 2026-11-07

An isolated TypeScript **7.0.2** installation passed `tsc -b --force --pretty false` over a temporary copy of the current application, Vite config and project configs, using the existing dependency tree. No application or semantic compiler-option changes were needed; only build-info paths were redirected into the temporary directory. Both project build-info files report 7.0.2 without errors. This was a compiler compatibility check, not a full dual-version toolchain validation or performance benchmark. Branch dependencies remain on TypeScript 6.0.3.

The remaining migration is tooling. The current ESLint config uses `strictTypeChecked`, `stylisticTypeChecked` and `projectService`, which require the TypeScript 6 compiler API. TypeScript 7.0 does not supply that API. Microsoft documents aliases that let the native compiler own `tsc` while existing API consumers continue to import TypeScript 6:

```json
{
  "@typescript/native": "npm:typescript@7.0.2",
  "typescript": "npm:@typescript/typescript6@6.0.2"
}
```

The compatibility package supplies `tsc6` and re-exports the older compiler API. This is a possible follow-up, not the installed configuration. [Microsoft's side-by-side instructions](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/#running-side-by-side-with-typescript-6.0).

Adopting it would require reviewing the new lockfile and transitive compiler dependency, verifying the compiler binaries and typed lint resolution, documenting editor setup, and rerunning the existing native, Docker and CI checks plus browser smoke tests. Native platform packages need verification on macOS arm64 and the Linux environments used by Docker/CI. The recommendation remains to keep TypeScript 6 for this consolidation and handle the dual-version setup separately if useful. Both projects use `noEmit`, so Vite still creates the browser bundle; no new browser or device functionality follows from this compiler change.

## Physical validation and deferred defects — 2026-11-07–12

Reported browser: **Microsoft Edge 156.0.4314.58 (Official build), arm64, on macOS** on November 7; its version was not reconfirmed on November 12. Hardware was a WeAct STM32H743 with carrier signal jumpers and a Fanatec wheelbase. The November 12 mapping tests used the contributor's **0.6.3 reset-diagnostics build** from [PR #64](https://github.com/Gugic/fanadapter/pull/64). The firmware version for the earlier output-only run was not recorded.

The contributor reported these successful checks:

- Live outputs, Direct output control, Sequential and Test axes registered through the wheelbase in a Fanatec application on Windows.
- Change a setting, Save, disconnect/reconnect, power-cycle, confirm persistence and restore its original value.
- Cancel the device picker, reconnect after Disconnect, and recover from USB unplug/replug without restarting the browser or leaving the port occupied.
- Repeat connection/edit/output checks against `make -C webconfig preview`; refresh while connected under `make dev` and reconnect without duplicate updates or an occupied port.
- Enumerate Fanatec ClubSport V3 pedals over USB and map brake and clutch successfully. The pedals were not simultaneously connected by RJ12.

Local-file flashing of official 0.6.2 and the contributor's 0.6.3 image worked, but DFU entry required power cycling and BOOT0. [Issue #63](https://github.com/Gugic/fanadapter/issues/63) reproduces missing DFU enumeration without a browser on both versions; PR #64 adds diagnostics rather than changing the handoff. The dependency change does not modify `dfu.ts`, `firmwareUpdate.ts`, firmware or the flashing flow. An unavailable Latest value during local development is expected without the same-origin `public/firmware/fanadapter-stm32.{json,bin}` release mirror.

**Throttle mapping remains a separate defect**, reproduced on both this branch and the published upstream application. Devices and Mappings show pedal movement, but Outputs remains zero and the binding disappears on reconnect. Releasing direct-output overrides did not resolve it. The captured calibration is within the protocol's 16-bit range. A real-device trace recorded a valid 206-byte `set_binding` line for throttle slot 0, VID/PID `3767:6203`, axis 0, `rawMin:63`, `rawMax:4095`, and `invert:false`; the sole pending request received `{"err":"bad_json"}`. The serial client resolves that error as success and updates its local binding. Reconnect readback confirms that firmware retained no throttle binding while brake and clutch remained populated, with no Save or clearing command between capture and reconnect. A simulated-adapter reproduction independently confirmed the misleading UI behavior.

Read-only device probes identified a matching USB receive defect. The same 206-byte version request succeeds in one write or with 63-, 65- or 100-byte chunks, but fails with 64- or 128-byte chunks, consistently across three runs. Flat JSON also fails at 64 bytes. A complete 64-byte version request produces **two replies**, whereas 63- and 65-byte requests each produce one, repeated twice. The configuration readback was unchanged and the port was closed after testing. The probes sent only `version` and `get_config`.

The pinned TinyUSB revision (`86ad6e56c1700e85f1c5678607a762cfe3aa2f47`) skips received-length correction for zero-length OUT packets, allowing 64 stale bytes into the CDC command stream. An offline model using the actual driver handlers, line assembler and parser reproduces the failure; the narrow fix passes under ASan/UBSan. Upstream already corrected this in [TinyUSB commit aa0fc2e](https://github.com/hathach/tinyusb/commit/aa0fc2e08f1c2dd6f026a431e8989357fbb4c5bf), merged through [PR #3293](https://github.com/hathach/tinyusb/pull/3293). Actual USB packets were not captured, so zero-length-packet delivery is inferred from the boundary tests and duplicated replies. A patched-firmware bench test is still required to confirm throttle recovery. Firmware backporting and webconfig error handling belong in separate follow-up work; neither fix is included here.

Remaining or unreported coverage includes handbrake mapping, hands-free DFU entry, flashing through the published manifest, source-edit/HMR recovery beyond page refresh, and the minimum Chromium 111 browser. Existing slider-crossing and dialog focus-return limitations are described above. These results provide partial physical compatibility coverage, not a claim that every device or firmware path works.

An opt-in hardware suite is deferred to a separate PR, tracked by [EpiJunkie/fanadapter #1](https://github.com/EpiJunkie/fanadapter/issues/1). Additional simulated persistence/readback, capture/recovery and firmware-dialog tests are also deferred. The four existing browser scenarios introduced for this dependency migration remain in this PR.
