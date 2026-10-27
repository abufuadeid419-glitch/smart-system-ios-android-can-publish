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
