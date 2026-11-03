# Malmesbury C of E Primary School website

The public website at https://malmesburyprimaryschool.co.uk.

- `content/` — the text of each page (Markdown).
- `assets/images/` — photos (shown on the site under `/images/photos/`); `assets/docs/` — downloadable documents (`/documents/`).
- `generator/` — a small Python script that turns the content into the website (`python generator/build.py` → `dist/`).
- `admin/` — the staff editor at `/admin`. Staff changes are proposals; they only go live after approval by the head, deputy head or business manager.
- `functions/api/` — the sign-in helper for the editor.

Hosting: Cloudflare Pages builds this repository automatically (build command `pip install -r requirements.txt && python generator/build.py`, output `dist`).

Please do not add photos in which children can be identified, or documents containing pupils' personal details.
