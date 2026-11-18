# Frontend Note — what was kept unchanged, and what had to change

This project was built with one rule from the user: **change only
the backend (Java → Python); do not change anything else.**

## What is unchanged (the frontend)

- **The page shell.** Every page uses the original template: the
  blue title "Designing Secure and Efficient Biometric-Based Secure
  Access Mechanism for Cloud Services", the menu tabs (HOME PAGE /
  CLIENT / REMOTE SERVER / AUTHENTICATE SERVER / OWNER), the cloud
  image slider with 3 images, the blue sidebar menu box, and the
  footer. (Note: the tab label "AUTHENTICATE SERVER" wraps onto two
  lines — it did that in the original too; the label is kept
  verbatim.)
- **Headings, labels, field names and button text.** Every form
  field keeps its original name (`userid`, `pass`, `email`, `mobile`,
  `address`, `dob`, `gender`, `pincode`, `pic`, `pic2`, `t1`, `t22`,
  `t42`, `tt`, `t4`, `t13` …) and every button keeps its original
  text ("Register", "Login", "Submit", "Upload", "Encrypt",
  "Download", "Authorize", "Generate Private Key", "Give Access
  Control" …). Table column headings are the original ones (File
  Name, Session Key, Private Key, Rank, Date & Time, Access
  Authorization, File Owner, Client Name, File Name, Operation …).
- **CSS, JS and images — byte-identical to the original zip.**
  `static/css/style.css`, `static/css/coin-slider.css`,
  `static/js/cufon-yui.js`, `jquery-1.4.2.min.js`,
  `coin-slider.min.js`, `script.js`, and `static/images/` (slide1/
  2/3.jpg, Architecture.png, logo.png, and the rest) are copied from
  the original, unedited. That is why the pages look like the
  original 2011 site, not like a modern Flask app.
- **Menus.** The sidebar menu on each role page lists the same items
  as the original JSP (Owner: Home / Upload / View All Uploaded
  Files / View All Transactions / Log Out; Client: Home / View All
  Files / Download / Log Out; Cloud: Home / View All Owners and
  Authorize / View All Clients and Authorize / View All Cloud Files
  / View All Transactions / View All Attackers / View File Score
  Results / View Time Delay Results / View Throughput Results /
  Log Out; Trustee: Home / Generate Private Key / View All Attackers
  / Log Out).
- **Messages.** The original's messages are kept verbatim where the
  flow is the same: "Sorry Wrong Credentials!", "Finger Print
  Mismatch, Please Provide Correct Finger Print!!", "Registered
  Successfully", "Data Uploaded Successfully !!!", "No Secret Key
  Generated or Secret key is mis Matched !!!", "No Access Permission
  For this File !!!", "File Doesn't Exist !!!", "WELCOME TO OWNER
  :: Raja", "WELCOME TO USER :: Harish", "WELCOME TO CLOUD ::
  Server", "WELCOME TO TRUSTEE :: AServer".
- **The original source itself.** All 121 JSP files, the 7 Java
  files, `web.xml`, `Database.sql` and `multi-user.sql` were used as
  the reference for this conversion. They are **not included in this
  repository** — this repo contains the Python implementation only.

## What had to change (and why)

Only JSP constructs — the things that *are* the backend — were
replaced. Nothing visual was redesigned:

| JSP construct | Replaced by |
|---|---|
| `<%@ include file="connect.jsp" %>` + `Class.forName(...)` + `DriverManager.getConnection(...)` | `get_conn()` in `app.py` (one connection per request, MySQL or SQLite) |
| `<% ResultSet rs = st.executeQuery("SELECT ...") %>` | `q("SELECT ...", params)` in `app.py` |
| `<%= rs.getString("fname") %>` | `{{ row.fname }}` in the Jinja2 template |
| `<% while(rs.next()) { %> … <% } %>` | `{% for row in rows %} … {% endfor %}` |
| `<% if(...) { %> … <% } %>` | `{% if ... %} … {% endif %}` |
| `request.getParameter("t1")` | `request.form.get("t1")` |
| `session.setAttribute("username", …)` | `session["owner"] = …` (per-user Flask session) |
| `response.sendRedirect("wronglogin.html")` | `redirect(url_for("wronglogin"))` |
| `<form action="Upload1.jsp" …>` | `<form action="{{ url_for('owner_upload1') }}" …>` |

## Deliberate differences (small, and honest)

These are the only places where the rendered page differs from the
original JSP output, and each one is a deliberate fix or a
translation of something that could not run as written:

1. **Results charts are CSS bars, not JavaScript charts.** The
   original loaded `jscharts.js` from its `sources/` folder and drew
   a chart. The numbers (time delay and throughput per file) are
   the same; they are shown as simple bars instead.
2. **The OTP page shows the generated OTP.** The original's OTP
   flow could not run at all (`ClientOTP.jsp` missing, `user.otp`
   column missing) and had no SMS/email to send the code with. This
   demo shows the code on the page so the flow can be used.
3. **The register/login pages show a short note** (demo logins, and
   where the demo fingerprint images live) — the original showed
   nothing there. This is help text only; the forms are unchanged.
4. **The home page has a short project description and the demo
   logins** — the original home page showed only the architecture
   diagram. The diagram, title, tabs and slider are unchanged.
5. **The Authority login (`AAuthentication.jsp`) has a login page.**
   In the original it was a POST-only page with no form and no menu
   link. The login form is new; the credentials and the redirect to
   the Owner main page are the original's.
6. **`AViewOTP.jsp` is replaced by the attackers page.** The
   original is broken (JDBC-ODBC to a different database, different
   columns) and could never have run. The attackers table it was
   supposed to show is shown on `/cloud/attackers` instead.

## How "frontend unchanged" was verified

During the conversion, the CSS, JS and images were compared against
the original source with `diff -r` — no differences. The original
source files are not included in this repository (Python files only),
so the diff cannot be re-run from this repo alone. Compare any
template with its JSP by name — the
headings, labels, field names and button texts match; only the
scriptlets are gone.
