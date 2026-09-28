# Google OAuth production readiness package

Checked 2026-09-28 against Google’s official documentation. This package does not submit an application or authorize an account.

## Exact runtime scopes

The code requests only:

- `https://www.googleapis.com/auth/gmail.readonly` — required to list threads/history and read message content for new inquiry and reply detection. Google classifies it as **Restricted**. `gmail.metadata` cannot provide the body required by the product, so it is not a functional replacement.
- `https://www.googleapis.com/auth/gmail.send` — required for the user-confirmed reply send. Google classifies it as **Sensitive**.

Calendar scope is not requested. `mail.google.com`, `gmail.modify`, `gmail.compose`, settings and delete permissions are not requested. Scope sources: [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

## Console submission checklist (OWNER ACTION)

1. Use a Production-only Google Cloud project. Verify the public domain in Search Console and configure the exact HTTPS homepage, privacy, terms, support email, authorized domain and `<BACKEND_URL>/gmail/callback` URI. Google requires a public homepage and same-domain privacy link: [brand verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification), [OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies).
2. Add only the two scopes above. Supply a reviewer test account, a video showing connection/read/user-confirmed-send/revoke/delete, and a justification explaining why message bodies make `gmail.metadata` insufficient.
3. Submit brand, Sensitive and Restricted scope verification. Because Restricted Gmail data is transmitted to and stored by the backend, plan for the independent security assessment and annual reassessment unless Google records an applicable exception: [verification requirements](https://support.google.com/cloud/answer/13464321?hl=en), [verification FAQ](https://support.google.com/cloud/answer/13463817?hl=en).

## Data-use explanation

Profit Radar uses Gmail message/thread identifiers, headers and content only to detect the signed-in company’s sales follow-ups, show source evidence, generate a reviewable draft, send only after explicit confirmation, detect replies and maintain the associated timeline. It does not sell Google user data, use it for advertising, or allow an AI instruction embedded in email to change authorization. Tokens are backend-only, encrypted at rest with versioned keys, refreshed server-side, never returned to the browser, and removed during disconnect/account deletion. The public privacy policy must name the actual processors, retention and international-transfer terms and include Google API Services User Data Policy Limited Use language approved by counsel.

## Release gate

Do not invite external customer accounts until the Console shows the exact Production client, domain, branding and scopes as approved and the security-assessment outcome is documented. TEST-user success is not approval.
