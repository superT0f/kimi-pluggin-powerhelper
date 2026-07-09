# Design : `hi-there` — daily terminal dashboard for PowerHelper

## Objectif

Ajouter au plugin **PowerHelper** un Skill `hi-there` qui affiche un tableau de bord quotidien dans le terminal. Le rendu est entièrement en anglais et comprend :

1. Un **ASCII meme** amusant.
2. La **météo** de Combs-la-Ville (77380).
3. Quelques **headlines** publiques synthétisées.
4. Un **cache** local valable 24h pour réduire la consommation de tokens et les appels réseau.

## Contexte

Le plugin PowerHelper existe déjà avec :

- `kimi.plugin.json`
- `skills/using-powerhelper/SKILL.md`
- `commands/hello.md`
- `README.md`

On ajoute ici un second Skill et une seconde commande slash au même plugin.

## Architecture

Approche retenue : **Skill + script Python local**.

- Le `SKILL.md` décrit quand et comment invoquer le dashboard.
- Un script Python `tools/hi-there.py` gère le cache, les appels réseau, le parsing et le formatage.
- Kimi Code appelle le script via l’outil `Bash`, puis affiche la sortie brute.

Cette approche minimise les tokens consommés par le modèle : le LLM ne fait que lancer le script et relayer le résultat.

## Structure du repo mise à jour

```
kimi-pluggin-powerhelper/
├── README.md
├── kimi.plugin.json
├── skills/
│   ├── using-powerhelper/
│   │   └── SKILL.md
│   └── hi-there/
│       └── SKILL.md
├── commands/
│   ├── hello.md
│   └── hi-there.md
└── tools/
    └── hi-there.py
```

## Composants

### 1. `tools/hi-there.py`

Script Python 3 autonome. Responsabilités :

- Accepter un argument optionnel `location` (défaut : `Combs-la-Ville`).
- Gérer un cache JSON dans `~/.cache/powerhelper/hi-there.json`.
- Si le cache a moins de 24h, l’utiliser.
- Sinon :
  - Récupérer la météo via `https://wttr.in/{location}?format=3`.
  - Récupérer les headlines via `http://feeds.bbci.co.uk/news/rss.xml` (3–5 items).
  - Choisir un meme ASCII aléatoire dans une liste interne.
  - Écrire le cache.
- Afficher une page terminal formatée en anglais.

Format de sortie (exemple) :

```text
┌─────────────────────────────────────────────┐
│  ☀️  Good Morning! Here's your daily briefing │
├─────────────────────────────────────────────┤
│                                             │
│        (ASCII meme ici)                     │
│                                             │
├─────────────────────────────────────────────┤
│  🌤️ Weather in Combs-la-Ville                │
│     Partly cloudy +14°C                     │
├─────────────────────────────────────────────┤
│  📰 News                                    │
│     • Headline 1                            │
│     • Headline 2                            │
│     • Headline 3                            │
├─────────────────────────────────────────────┤
│  Run /powerhelper:hi-there for a fresh page  │
└─────────────────────────────────────────────┘
```

### 2. `skills/hi-there/SKILL.md`

Skill directory-form avec frontmatter :

- `name` : `hi-there`
- `description` : résumé pour le modèle
- `type` : `prompt`
- `whenToUse` : contexte d’activation
- `arguments` : `location` (optionnel)

Body : instructions pour appeler le script via Bash avec `${KIMI_SKILL_DIR}/../tools/hi-there.py $location`, puis afficher la sortie exacte.

### 3. `commands/hi-there.md`

Slash command `/powerhelper:hi-there`.

Frontmatter avec `description`. Body : prompt qui appelle le script et affiche le dashboard.

### 4. `kimi.plugin.json`

Aucune modification requise : les champs `skills` et `commands` pointent déjà sur les répertoires qui contiendront les nouveaux fichiers.

### 5. `README.md`

Ajouter une section `hi-there` décrivant :

- la commande `/powerhelper:hi-there` ;
- l’activation naturelle (`good morning`, `daily briefing`, etc.) ;
- la dépendance Python 3 ;
- le fonctionnement du cache (24h).

## Data flow

1. L’utilisateur invoque `/powerhelper:hi-there` ou dit « good morning ».
2. Kimi Code charge le Skill `hi-there`.
3. Le Skill exécute `python3 ${KIMI_SKILL_DIR}/../tools/hi-there.py [location]` via Bash.
4. Le script lit le cache.
5. Si le cache est frais (< 24h), il est retourné tel quel.
6. Sinon :
   - fetch météo wttr.in ;
   - fetch RSS BBC News ;
   - sélectionne un meme ASCII ;
   - écrit le cache ;
   - retourne la page.
7. Kimi Code affiche la page dans le terminal.

## Error handling

- `wttr.in` indisponible : afficher `Weather unavailable` et continuer.
- RSS news inaccessible : afficher `News unavailable` et continuer.
- Cache corrompu : le supprimer silencieusement et refetch.
- Python 3 manquant : documenter la dépendance dans le README ; le skill peut éventuellement retomber sur une version sans script.

## Testing

- Exécuter `python3 tools/hi-there.py` directement et vérifier le rendu.
- Vérifier la création du cache après le premier run.
- Vérifier que le second run utilise le cache.
- Invoquer `/powerhelper:hi-there` dans Kimi Code CLI et vérifier l’affichage.
- Vérifier `/plugins info powerhelper` : aucune erreur de diagnostic.

## Propositions créatives (hors scope immédiat)

- Ajouter une citation quotidienne (`quote of the day`).
- Ajouter un agenda simplifié via un fichier `~/.cache/powerhelper/agenda.json` éditable par l’utilisateur.
- Ajouter un compteur de tâches du jour.
- Support de plusieurs sources de news via argument (`--source bbc|reuters`).
