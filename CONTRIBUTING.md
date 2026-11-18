# Contributing

Thanks for helping with this project. It is a student demo built by
converting a Java/JSP project to Python — please keep it simple and
honest.

## How to contribute

1. Fork the repo and create a branch for your change
   (`git checkout -b fix/otp-message`).
2. Make **one change per pull request** — one bug fix or one small
   feature.
3. **Do not change the frontend** unless the PR is specifically about
   it. The templates and `static/` files are a faithful copy of the
   original 2011 JSP frontend; restyling belongs in a separate PR with
   before/after screenshots.
4. Keep the demo working: after your change, run the app with
   `DB_TYPE=sqlite python app.py` and walk the demo flow
   (Raja uploads → Trustee generates key → Cloud gives access →
   Harish downloads). If a flow breaks, the PR is not ready.
5. If behaviour changes, update `README.md` (and `CODE_EXPLANATION.md`
   if the change affects how the code maps to the original Java).
6. Do not commit secrets: no real passwords, no `app.db`, no `instance/`,
   no `.env`. See `.gitignore`.

## Reporting bugs

Open an issue with:

- what you did (exact steps / which login),
- what you expected,
- what happened (paste the **last lines** of the terminal output),
- whether you ran it with MySQL or SQLite.

## What not to do

- Do not claim the fingerprint matching is real biometric recognition —
  it is file-name / identical-bytes matching, not minutiae extraction.
  See `README.md` → "Honest notes".
- Do not add real personal data or real fingerprint images.
- Do not "fix" the demo logins by removing them — they are the seed
  data from the original project's `Database.sql`.
