# Running on the workshop VDI

Everything you built on Windows works here. The VDI is Linux, so the commands
change slightly, but not a single line of application code does.

---

## First: the two repositories

This trips up almost everyone.

| Repository | What it is | Do you edit it? |
|---|---|---|
| `citi/coding-workshop-participant` | The **workshop's** repo. Setup scripts, validation, instructions. You cloned this on day one. | No |
| `meetsaurabhh/acme-project-tracker` | **Your project.** Everything you have built. | Yes |

Yesterday's commands configured the *machine*. They did not create your
application. Your application is on GitHub and you are about to clone it.

> **Ask your instructor one question before you go further:** should your
> submission live inside the `coding-workshop-participant` folder, or is a
> separate repository fine? Some workshops validate a specific folder
> structure. Five seconds of asking beats an hour of restructuring later.

---

## Step 1 — Open a terminal on the VDI

Click the nine-dot applications icon at the bottom of the desktop, then
Terminal.

Check the machine is ready:

```bash
python3 --version
node --version
psql --version
```

Three version numbers and you are set. If any are missing, the workshop's setup
script has not finished — run it again:

```bash
cd ~/coding-workshop-participant
source ~/.bashrc
./bin/setup-environment.sh -d
```

---

## Step 2 — Clone your project

```bash
cd ~
git clone https://github.com/meetsaurabhh/acme-project-tracker.git
cd acme-project-tracker
```

GitHub will ask for a username and a **password**. That password is not your
account password — it is a Personal Access Token.

**To create one:** on your own laptop, go to
https://github.com/settings/tokens → Generate new token (classic) → tick the
**repo** checkbox → Generate → copy it.

Paste it as the password. Then tell git to remember it so you only do this
once:

```bash
git config --global credential.helper store
```

---

## Step 3 — Run the setup script

```bash
chmod +x scripts/setup-vdi.sh
./scripts/setup-vdi.sh
```

It checks the tools, starts PostgreSQL, creates the `acme_pm` database, writes
a `.env` with a freshly generated secret, installs both sets of dependencies,
and loads the demo data.

Expect three to five minutes. It will ask for your `sudo` password — the same
one you used to log in to the VDI. Nothing appears as you type; that is
deliberate. Type it and press Enter.

---

## Step 4 — Start the application

Two terminals. In the VS Code terminal panel, the `+` icon opens a second one.

**Terminal 1 — backend**

```bash
cd ~/acme-project-tracker/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 — frontend**

```bash
cd ~/acme-project-tracker/frontend
npm run dev
```

Open **http://localhost:3030** in the VDI's browser and sign in with
`admin@acme.com` / `Admin@123`.

---

## Windows to Linux, command by command

The only things that change.

| On Windows | On the VDI |
|---|---|
| `.\.venv\Scripts\activate` | `source .venv/bin/activate` |
| `python` | `python3` |
| `dir` | `ls` |
| `Get-Content .env` | `cat .env` |
| `Remove-Item -Recurse -Force x` | `rm -rf x` |
| `$env:VAR="value"` | `export VAR="value"` |
| `Get-Service postgresql*` | `sudo systemctl status postgresql` |
| `Start-Service postgresql-x64-18` | `sudo systemctl start postgresql` |
| pgAdmin | `psql -U acme -d acme_pm` |
| `Ctrl + C` to stop a server | same |

Paths use forward slashes, and `~` means your home folder.

---

## Doing it manually, if the script fails

**Start PostgreSQL**

```bash
sudo systemctl start postgresql
pg_isready
```

**Create the database**

```bash
sudo -u postgres psql -c "CREATE USER acme WITH PASSWORD 'acme';"
sudo -u postgres psql -c "CREATE DATABASE acme_pm OWNER acme;"
```

**Write the .env file**

```bash
cd ~/acme-project-tracker/backend
cat > .env << 'EOF'
DATABASE_URL=postgresql+psycopg2://acme:acme@localhost:5432/acme_pm
JWT_SECRET=pick-any-long-random-string-here
CORS_ORIGINS=http://localhost:3030
EOF
```

**Backend**

```bash
cd ~/acme-project-tracker/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seeds.seed_data
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd ~/acme-project-tracker/frontend
npm install
npm run dev
```

---

## Looking at the database

There is no pgAdmin here, so use the command line:

```bash
psql -U acme -d acme_pm -h localhost
```

Useful commands once you are in:

```
\dt                        list the tables
SELECT * FROM projects;    see every project
\q                         quit
```

Showing a row here right after creating it in the UI is a strong demo move.

---

## Working day to day

**Every time you sit down:**

```bash
cd ~/acme-project-tracker
sudo systemctl start postgresql    # only if it is not already running
```

Then the two terminals from Step 4.

**Committing your work:**

```bash
cd ~/acme-project-tracker
git add -A
git commit -m "What you changed"
git push
```

**Opening the project in an editor:** the workshop installed VS Code, PyCharm
and IntelliJ. For VS Code:

```bash
code ~/acme-project-tracker
```

---

## Deploying to LocalStack

Your organisers had you set up a LocalStack token, which strongly suggests this
is the expected deployment target. The Terraform and scripts are already in
your repo.

Check the token is in place:

```bash
echo $LOCALSTACK_AUTH_TOKEN
```

Nothing printed? Add it:

```bash
echo "export LOCALSTACK_AUTH_TOKEN='ls-your-token'" >> ~/.bashrc
source ~/.bashrc
```

Then follow `docs/DEPLOY-LOCALSTACK.md`. Use the bash version of the deploy
script:

```bash
./scripts/deploy-localstack.sh
```

---

## When something breaks

| Message | Fix |
|---|---|
| `psql: could not connect to server` | `sudo systemctl start postgresql` |
| `password authentication failed for user "acme"` | Rerun the two `CREATE` commands above |
| `permission denied: ./scripts/setup-vdi.sh` | `chmod +x scripts/setup-vdi.sh` |
| `Port 3030 is already in use` | `lsof -ti:3030 \| xargs kill -9` |
| `Port 8000 is already in use` | `lsof -ti:8000 \| xargs kill -9` |
| `ModuleNotFoundError` | You forgot `source .venv/bin/activate` |
| `command not found: python` | Use `python3` |
| git asks for a password repeatedly | `git config --global credential.helper store` |

---

## Nothing was wasted

Every hour on your laptop produced something that transfers unchanged:

- The application itself, all 59 backend files and 15 frontend files
- The layered architecture
- Your commit history, which is evidence of how you worked
- The Terraform, the deployment scripts, the documentation

The only genuinely new thing is a handful of Linux commands. The hard part —
building it — is already done.
