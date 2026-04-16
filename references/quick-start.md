# GitHub Sync — Quick Start

## For the user (Valeriu)

### First-time setup on a new PC

1. Install Git: https://git-scm.com/download/win
2. Configure credentials:
   ```powershell
   git config --global user.name "Valeriu Filip"
   git config --global user.email "filip.valeriu@gmail.com"
   git config --global credential.helper manager
   ```
3. Clone any repo and push once — Windows Credential Manager will save the PAT:
   ```powershell
   git clone https://filipvaleriu@github.com/filipvaleriu/REPO.git
   # When prompted for password, paste your PAT
   ```

### Generate a new PAT (if expired)

1. Go to: https://github.com/settings/tokens?type=beta
2. Generate new token:
   - Name: `cowork-sync` (or whatever you prefer)
   - Expiration: 90 days recommended
   - Repository access: All repositories
   - Permissions: Contents (Read and write), Metadata (Read-only)
3. Copy the token immediately — it won't be shown again
4. Provide it to Claude in Cowork when asked

### Your repositories

| Repo | Visibility | Purpose |
|------|-----------|---------|
| project-tracker-skill | Public | Skill: project dashboard generator |
| Marketing-FGO | Private | FGO marketing analytics & campaigns |
| Conversii-Orange | Private | Orange conversion analysis |
| export-SAGA | Private | SAGA export tools |
| analiza-vanzari | Private | Sales analysis |
| SpaceRentManager | Private | Tenant-landlord expense tracker |
| AnalizaStocuri-ImmClub | Private | Inventory analysis |
| AlerteTicketeSuport | Private | Support ticket alerts |
| Administrative | Private | Administrative tools |
| orchestration | Public | Orchestration scripts |

## For Claude (in Cowork sessions)

### Before any git operation

1. Check if user has provided a PAT in this session
2. If not, ask: "Am nevoie de GitHub PAT-ul tău pentru a sincroniza cu GitHub. Îl ai la îndemână?"
3. Get a browser tab ready: `tabs_context_mcp` → navigate to `https://github.com`
4. Test the token with a quick user info call before proceeding

### Common user requests → actions

| User says | Action |
|-----------|--------|
| "push to GitHub" | Batch commit (operation 7) |
| "sync my project" | Compare local vs remote, push differences |
| "pull latest" | Read files from repo, write locally |
| "create a repo" | POST /user/repos |
| "what repos do I have" | GET /user/repos |
| "backup this" | Create repo if needed + push all files |
