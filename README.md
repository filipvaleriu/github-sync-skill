# github-sync-skill

Skill Cowork pentru operatii Git/GitHub (commit, push, pull, create repos) via GitHub REST API,
executat prin Claude in Chrome pentru a ocoli restrictiile de retea ale sandbox-ului.

## Structura

```
github-sync-skill/
├── SKILL.md              # Instructiuni principale skill
├── README.md             # Acest fisier
└── references/
    └── quick-start.md    # Ghid rapid: setup PAT, repo list, comenzi frecvente
```

## Instalare in Cowork

Deschide `../skills/github-sync.skill` din Cowork — se instaleaza automat.

## Prerequisite

- GitHub Personal Access Token (Fine-grained) cu permisiuni Contents (Read and write)
- Token-ul se furnizeaza per-sesiune Cowork, nu se hardcodeaza

## Operatii suportate

| Operatie | Metoda API |
|----------|-----------|
| List repos | GET /user/repos |
| Create repo | POST /user/repos |
| List files | GET /repos/{owner}/{repo}/contents/{path} |
| Read file | GET /repos/{owner}/{repo}/contents/{path} |
| Create/Update file | PUT /repos/{owner}/{repo}/contents/{path} |
| Delete file | DELETE /repos/{owner}/{repo}/contents/{path} |
| Batch commit (multi-file) | Git Trees API (blobs + tree + commit + ref update) |

## Changelog

- 2026-04-16: v1.0 — creat si testat pe repos filipvaleriu/* (read, write, delete confirmate)
