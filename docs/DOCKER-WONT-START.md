# Docker says "Virtualisation support not detected"

Work through this in order. Stop as soon as the app is running.

---

## Step 0: Find out which problem you have

Press `Ctrl + Shift + Esc` to open Task Manager → **Performance** tab → click
**CPU** on the left. Look at the bottom-right block of text for a line labelled
**Virtualization**.

| What you see | Go to |
|---|---|
| `Virtualization: Disabled` | Fix A |
| `Virtualization: Enabled` | Fix B |
| No such line at all | Fix C |

If you are on a **work or university laptop**, expect Fix C. Do not spend an
hour fighting it — Fix C works fine and takes fifteen minutes.

---

## Fix A — Turn virtualization on in the BIOS

Your CPU can do it, but the setting is switched off at the firmware level.
Windows cannot change this; you have to do it before Windows loads.

1. Save any open work. Close everything.
2. Click **Start → Settings → System → Recovery**.
3. Next to **Advanced startup**, click **Restart now**. Confirm.
4. The machine reboots into a blue menu. Choose:
   **Troubleshoot → Advanced options → UEFI Firmware Settings → Restart**
5. You are now in your BIOS. It looks nothing like Windows — that is normal.
   Navigate with the arrow keys; the on-screen legend tells you which keys do
   what.
6. Find the setting. It hides in different places on different machines. Look
   under **Advanced**, **CPU Configuration**, **Security**, or
   **Virtualization**. The setting is called one of:
   - `Intel Virtualization Technology` or `Intel VT-x` (Intel machines)
   - `SVM Mode` or `AMD-V` (AMD machines)
7. Change it from **Disabled** to **Enabled**.
8. Press the key for **Save and Exit** (usually `F10`), confirm, let Windows
   boot.

**If step 3-4 does not show "UEFI Firmware Settings":** restart the machine and
press the BIOS key repeatedly as it powers on. The key is `F2`, `F10`, `Del` or
`Esc` depending on the maker — Dell and Lenovo usually `F2`, HP usually `Esc`
then `F10`, ASUS and MSI usually `Del`.

Now open Docker Desktop again. If it still complains, do Fix B as well.

---

## Fix B — Turn on the Windows components Docker needs

Virtualization is on, but Windows is missing the pieces that use it.

1. Click **Start**, type `Windows features`, open **Turn Windows features on or
   off**.
2. Tick these boxes:
   - **Virtual Machine Platform**
   - **Windows Subsystem for Linux**
   - **Hyper-V** (if it is in the list — Windows Home does not have it, that is
     fine, skip it)
3. Click OK and **restart the computer** when asked. The restart is required.
4. After it comes back, open PowerShell **as Administrator** (right-click Start
   → Terminal (Admin)) and run:

   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

5. Restart once more, then open Docker Desktop.

---

## Fix C — Run the app without Docker at all

Docker is a convenience, not a requirement. The app runs perfectly well
without it. You will install two things instead, neither of which needs
virtualization or admin rights in most setups.

### C1. Install Python and Node

- **Python 3.12** — https://www.python.org/downloads/
  On the first screen of the installer, **tick "Add python.exe to PATH"**
  before clicking Install. This one checkbox causes most beginner problems when
  missed.
- **Node.js 20 LTS** — https://nodejs.org (take the LTS button)

Check both worked. Open a **new** PowerShell window and run:

```powershell
python --version
node --version
```

Two version numbers means you are good.

### C2. Get a PostgreSQL database

Pick whichever you can actually do on your machine.

**Option 1 — free cloud database (easiest, no install, works on locked-down laptops)**

1. Go to https://neon.com and sign up. The free tier is enough.
2. Create a project. It hands you a connection string that looks like:
   `postgresql://myuser:mypassword@ep-cool-name-123.aws.neon.tech/neondb?sslmode=require`
3. **Insert `+psycopg2` after `postgresql`** so it becomes:
   `postgresql+psycopg2://myuser:mypassword@ep-cool-name-123.aws.neon.tech/neondb?sslmode=require`
4. Keep that string handy. That is your `DATABASE_URL`.

**Option 2 — install PostgreSQL locally**

1. Download from https://www.postgresql.org/download/windows/
2. Run the installer. When it asks for a password for the `postgres` user, set
   it to something you will remember. Leave the port as `5432`.
3. After install, open **pgAdmin** (it comes with it), connect, right-click
   **Databases → Create → Database**, name it `acme_pm`.
4. Your connection string is:
   `postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/acme_pm`

### C3. Start the backend

Open PowerShell, go to the project folder, and run these one at a time:

```powershell
cd C:\path\to\acme-pm\backend

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

$env:DATABASE_URL="PASTE_YOUR_CONNECTION_STRING_HERE"
$env:JWT_SECRET="any-long-random-text-you-like"

python -m app.seed
uvicorn app.main:app --reload
```

The last command prints `Uvicorn running on http://127.0.0.1:8000`.
**Leave this window open.** Closing it stops the backend.

Check it: open http://localhost:8000/docs in your browser. You should see the
API documentation page.

> If `.venv\Scripts\activate` is refused with a message about execution
> policies, run this once and try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### C4. Start the frontend

Open a **second** PowerShell window (leave the first one running):

```powershell
cd C:\path\to\acme-pm\frontend

npm install
copy .env.example .env
npm run dev
```

It prints `Local: http://localhost:5173/`. Open that in your browser and sign
in with `admin@acme.com` / `Admin@123`.

### C5. Every time you come back to it

You need both windows again:

```powershell
# Window 1
cd C:\path\to\acme-pm\backend
.venv\Scripts\activate
$env:DATABASE_URL="PASTE_YOUR_CONNECTION_STRING_HERE"
uvicorn app.main:app --reload

# Window 2
cd C:\path\to\acme-pm\frontend
npm run dev
```

You only run `python -m app.seed` again if you want to wipe the data and start
fresh.

---

## On a Mac?

This error means Docker Desktop cannot reach the hypervisor. Quit Docker
Desktop fully, reopen it, and if it persists, reinstall it. On Apple Silicon
also check **Settings → General → Virtual Machine Service** is not disabled.
If none of that works, Fix C above applies to you too — the commands are the
same except:

```bash
source .venv/bin/activate      # instead of .venv\Scripts\activate
export DATABASE_URL="..."      # instead of $env:DATABASE_URL="..."
cp .env.example .env           # instead of copy
```

---

## What to tell IT, if you need to ask

> I need hardware virtualization (Intel VT-x / AMD-V) enabled in the BIOS, and
> the Virtual Machine Platform and Windows Subsystem for Linux features turned
> on, so I can run Docker Desktop for a development workshop.

If the answer is no, use Fix C and move on. Nothing in the workshop brief
requires Docker.
