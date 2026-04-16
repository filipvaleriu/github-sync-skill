# incrementality-analysis-skill

Skill Cowork pentru analiza impactului incremental al interventiilor (echipa de vanzari,
campanii, canale partener) asupra ratelor de conversie. Genereaza rapoarte HTML interactive
cu grafice si tabele, gata de prezentat stakeholderilor.

## Structura

```
incrementality-analysis-skill/
├── SKILL.md                          # Instructiuni principale
├── README.md                         # Acest fisier
├── scripts/
│   └── incrementality_report.py      # Script generare raport HTML
└── references/
    └── html_template.md              # Template HTML cu sidebar metodologie
```

## Instalare in Cowork

Deschide `../skills/incrementality-analysis.skill` din Cowork.

## Ce face

- Separa conversii organice de cele influentate
- Compara grupuri contacted vs non-contacted (Baseline-A si Baseline-B)
- Calculeaza lift incremental, NNT (Number Needed to Treat), ROI
- Genereaza raport HTML interactiv cu grafice

## Changelog

- 2026-04-16: Reorganizat in repo separat conform conventiei skills
