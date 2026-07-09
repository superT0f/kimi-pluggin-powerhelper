# Design : PowerHelper — plugin « hello world » pour Kimi Code CLI

## Objectif

Créer un plugin Kimi Code CLI minimaliste mais complet, destiné à monter en compétence sur le mécanisme des plugins personnalisés. Le plugin embarque à la fois :

1. un **Agent Skill** chargé automatiquement au démarrage de session ;
2. une **slash command** invoquable manuellement.

Aucun code exécutable (MCP, hooks) n’est inclus dans cette première version, afin de se concentrer sur le format de manifeste, le format `SKILL.md` et l’installation.

## Contexte

Le dossier de travail est vide. Le dépôt distant est créé :
`git@github.com:superT0f/kimi-pluggin-powerhelper.git`.

## Structure du repo

```
kimi-pluggin-powerhelper/
├── README.md
├── kimi.plugin.json
├── skills/
│   └── using-powerhelper/
│       └── SKILL.md
└── commands/
    └── hello.md
```

## Composants

### 1. `kimi.plugin.json` — manifeste du plugin

Champs requis et utiles :

- `name` : `powerhelper` (id du plugin, utilisé pour namespacer la commande).
- `version` : `0.1.0`.
- `description` : description du plugin.
- `skills` : `"./skills/"` — dossier contenant le Skill.
- `sessionStart.skill` : `"using-powerhelper"` — Skill injecté au démarrage.
- `commands` : `"./commands/"` — dossier contenant les commandes.
- `interface.displayName` : `"PowerHelper"`.
- `interface.shortDescription` : résumé affiché dans `/plugins`.

### 2. `skills/using-powerhelper/SKILL.md` — Skill automatique

Format directory-form recommandé.

Frontmatter :

- `name` : `using-powerhelper`
- `description` : résumé pour le modèle
- `type` : `prompt`
- `whenToUse` : contexte d’activation automatique

Body : instructions concises pour que Kimi Code :

- réponde « Hello, World! from PowerHelper 👋 » sur une salutation ;
- explique brièvement le plugin et la commande `/powerhelper:hello` si on lui demande ce qu’il fait ;
- reste court.

### 3. `commands/hello.md` — slash command

Commande accessible via `/powerhelper:hello` après installation.

Frontmatter :

- `description` : description affichée dans la liste des commandes.

Body : prompt demandant à Kimi Code d’afficher le message hello-world.

### 4. `README.md` — documentation pédagogique

Contenu prévu :

- qu’est-ce qu’un plugin Kimi Code ;
- à quoi servent les Skills et les slash commands ;
- structure du repo ;
- installation en local (`/plugins install ./kimi-pluggin-powerhelper`) ;
- installation depuis GitHub (`/plugins install https://github.com/superT0f/kimi-pluggin-powerhelper`) ;
- commandes disponibles ;
- ressources et liens officiels.

## Flux d’utilisation

1. L’utilisateur installe le plugin.
2. Après `/reload`, le Skill `using-powerhelper` est injecté dans le contexte système.
3. Une salutation comme « hello » déclenche automatiquement la réponse du Skill.
4. L’utilisateur peut aussi taper `/powerhelper:hello` pour forcer le message.

## Validation

Après implémentation et installation locale :

- `/plugins info powerhelper` ne doit afficher aucune erreur de diagnostic.
- Dire « hello » doit déclencher la réponse du Skill.
- `/powerhelper:hello` doit afficher le message attendu.

## Étapes suivantes (hors scope)

- Ajouter un serveur MCP stdio pour illustrer les vrais outils.
- Ajouter un hook de cycle de vie (`PreToolUse`, etc.).
