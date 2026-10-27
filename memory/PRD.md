# النظام الذكي (Smart System) — Cloned App

## Original Problem Statement
Clone https://github.com/abufuadeid419-glitch/apk-ios-ready-to-test.git, use the existing Convex database (fearless-ostrich-878) and the SMS gateway account; make it secure end to end with no issues. User choices: keep Convex; SMS for login codes; after entering the code the user sets a password, later logins with the same number ask for the password; same features + bug/security fixes + refreshed look.

## Architecture
- Expo Router (SDK 58) Arabic RTL app, ~30 screens across owner / acct / dist / dev roles.
- Backend: Convex (`frontend/convex/*`), REST under `https://fearless-ostrich-878.eu-west-1.convex.site/api`. FastAPI is a stub.
- Secrets: CONVEX_DEPLOY_KEY, SMS_GATE_USERNAME, SMS_GATE_PASSWORD in backend/.env (secure store) and synced into Convex env. Deploy: `cd frontend && set -a && . ../backend/.env && set +a && npx convex deploy -y`.

## Implemented (2026-06)
- Full repo cloned into workspace, deps installed for SDK 58, bundle id kept, Convex redeployed.
- Phone + password auth: `/auth/start` (password or SMS code), `/auth/password/login` (scrypt hashes in separate `user_passwords` table, 5 fails → 15 min lock, constant-time compare), `/auth/password` (set only when none exists or within 15 min of SMS login; signs out other devices). Forgot password via SMS code. Existing users without a password are asked to set one.
- Account deletion removes password records. Test seed resets the test org to ACTIVE.
- Original navy + coral palette restored (user request); green refresh reverted.
- Testing: iteration_1 + iteration_2 passed.

## Backlog
- P1: "Change password" inside settings (with current password).
- P1: Persist pending reset in /auth/me so an app restart mid-reset still asks for the new password.
- P2: Compact login layout so phone field isn't under sticky button on small screens; 44px touch targets on small buttons.

## Iteration 2026-06 (b)
- Change password in account sheet (current password required, 5-fail lock shared).
- Pro / VIP plans fully developer-controlled: tier, max employees, max distributors, per-feature modules (reports, targets, routes, tracking, daily_sms, debt_sms); developer can override per company. Backend gating via hasFeature.
- Keyboard: sheets use keyboard-controller KeyboardAvoidingView (no double lift); login hero static & compact; phone field first.
- Android: SystemUI root background = surface, KeyboardProvider translucent bars.
- New logo applied (icon, adaptive icon #021041, favicon, native splash) + animated JS splash matching mockup.
- Tests: iterations 3 & 4 passed.

## Backlog
- P2: Restyle buttons/accents to the new blue brand (optional).
- P1: Persist pending password reset across app restart.

## Iteration 2026-06 (c)
- iOS-style floating pill bottom navigation (FloatingTabBar) for Android / iOS<26 / web; iOS 26+ keeps NativeTabs. Active capsule, navy outline icons, Arabic labels, RTL, hides while keyboard open, sits above system nav bar.
- useBottomChrome reserves floating bar space so list ends are never hidden; KeyboardScreen footer offset updated; update banner placed above bar.
- Tests: iteration 5 passed (all roles); web shadow fixed after.

## Backlog
- Customers search empty state should say "no results" instead of "add your first customer".

## Iteration 2026-06 (d) — Billing system
- convex/billing.ts: Free/Pro/VIP plans with draft→publish, version history + restore, archive; payment methods + QR (Convex storage, magic-byte validation); owner payment requests with private receipts (JPG/PNG/WebP/PDF, PDF active-content quarantine, size limit), idempotency key, daily rate limit, price frozen at submission; developer review (PENDING/UNDER_REVIEW/NEEDS_INFO/APPROVED/REJECTED/CANCELLED/REFUNDED), idempotent atomic activation with grace period; manual plan assignment; audit_logs; stats; expiry reminder cron.
- Limits enforced server-side: employees, distributors, customers (Free plan limits from published FREE plan).
- Screens: src/screens/Subscription.tsx (owner /upgrade), src/screens/DevBilling.tsx (dev billing tab), OrgSubscription in org sheet.
- Tests: iteration 6 passed; tests/billing_smoke.py.

## Iteration 2026-06 (e) — Offline, returns, hardening
- Strict returns (returns.createSales): only products sold by same distributor to same customer, up to sold minus returned; concurrency-safe (Convex serializable mutations); quantity validation; sales quantity validation.
- voidSale refuses when returns depend on the sale.
- Offline: local return pre-check, dependency ordering over whole queue (customers → sales → returns), 409 conflicts kept in tray, rejected items drop optimistic rows + refetch, web online/offline listeners, 6-state SyncBadge with counts, readable failure reasons.
- Tests: tests/returns_validation.py 13/13, tests/void_guard.py 5/5, iterations 7–8 passed.

## Backlog / risks
- Free/Pro/VIP are drafts at price 0 and there are no active payment methods: developer must set prices, add a method and publish.
- Trial eligibility per plan, malware scanning (only signature checks), storage retention policy not implemented.
- Cross-distributor isolation verified by code review only (single test distributor).
- If a queued customer is permanently rejected, its dependent items still fail individually.
