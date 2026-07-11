# Sweetspot — Developer Onboarding Procedure

> **Owner:** Former user
> **Status:** Living document
> **Last updated:** Update as the project evolves.

---

## 1. Installations

### Visual Studio Code
Download and install Visual Studio Code.
- **Download:** Visual Studio Downloads for Windows
- **Installer:** Windows x64 User Installer

### Visual Studio
Download and install Visual Studio.
- **Download:** Microsoft Dev Essentials — Downloads — Visual Studio 2026
- **Version:** Visual Studio Professional 2026
- **License:** Required

### PostgreSQL Admin Tool — pgAdmin 4
Download and install pgAdmin 4.
- **Download:** pgAdmin 4 for Windows
- **Current version:** pgAdmin 4 v9.11, released Dec. 11, 2025

### Rancher Desktop
Download and install Rancher Desktop.
- **Download:** Rancher Desktop — Windows x64

### Redis Insight *(optional)*
- **Download:** Redis Insight
- **Current version:** 8.4

### Windows Subsystem for Linux 2 *(required)*
Install WSL from Microsoft Learn.

Run PowerShell as Administrator:

```powershell
wsl --install
```

### Node.js
Download and install Node.js.
- **Download:** Node.js Downloads

To fix the npm `UnauthorizedAccess` error, run:

```powershell
Set-ExecutionPolicy RemoteSigned
```

### Postman *(optional)*
- **Download:** Postman

### Bruno API Client
Download and install Bruno.
- **Download:** https://www.usebruno.com/downloads

### EF Core
Install EF Core version 10:

```bash
dotnet tool install --global dotnet-ef --version 10.*
```

### .NET SDK 10.0
Download and install .NET SDK 10.0.
- **Download:** Microsoft — Download .NET 10.0

### Azure CLI
Download and install Azure CLI.
- **Download:** Microsoft Learn — Install the Azure CLI

### VPN
Install and configure the VPN.
- **Reference:** VPN Installation — Windows Users

---

## 2. System Settings

### Windows Hosts File
Add the following custom localhost aliases to the Windows hosts file:

```text
127.0.0.1 redis
127.0.0.1 postgres
127.0.0.1 admin-api
127.0.0.1 bff-api
127.0.0.1 agent-api
127.0.0.1 audience-api
127.0.0.1 assets-api
127.0.0.1 applocal.sweetspot.com
```

---

## 3. Clone the Repository

Clone the Sweetspot repository:

```text
https://ClickDimensionstfs@dev.azure.com/ClickDimensionstfs/CRM/_git/sweetspot
```

---

## 4. Configure Local Environment Secrets

Set the Azure secret in:

```text
\ops\docker\local.env
```

> **Important:** Do not stage or commit your local secret changes.

Read the detailed instructions in `\ops\docker\local.env.README.md`.

To avoid accidentally staging or committing local secret changes, use Git's `skip-worktree` flag. From the repository root, run:

```bash
# Mark the file as "ignore my local edits" — local-only setting
git update-index --skip-worktree -- ops/docker/local.env

# Verify it — you should see an "S" prefix
git ls-files -v -- ops/docker/local.env
```

---

## 5. Start Redis and PostgreSQL Containers

Start the Redis and PostgreSQL containers:

```bash
docker compose up -d redis postgres
```

---

## 6. Generate Local HTTPS Certificates

Go to the following folder:

```text
\localhost-development-certs
```

Run this script in elevated PowerShell:

```powershell
setup-https.ps1
```

For more details, read `\localhost-development-certs\README.md`.

---

## 7. Start Sweetspot

### Redis and PostgreSQL
Make sure the Redis and PostgreSQL containers are running in Rancher Desktop.

### Back-End
Start the following projects as multiple startup projects:
- `SSP.BackendForFrontend.Api`
- `SSP.Agents.Api`
- `SSP.Admin.Api`

### Front-End
Go to the front-end root folder:

```text
\src\frontend
```

Install dependencies:

```bash
npm install
```

Start the front-end:

```bash
npm run start
```

---

**Reference:** https://chatgpt.com/share/e/6a46776c-9c1c-83eb-af64-71d937f2fff1
