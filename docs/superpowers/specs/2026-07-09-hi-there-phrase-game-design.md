# Design : Mini-jeu « Phrase of the Day » dans `hi-there`

## Objectif

Ajouter un mini-jeu de mémoire quotidien au Skill `hi-there` du plugin PowerHelper. Le jeu, entièrement en anglais, demande à l’utilisateur de se souvenir de la phrase qu’il a choisie la veille, puis de choisir la phrase du lendemain. Les victoires sont inscrites dans un fichier markdown local.

## Contexte

Le plugin PowerHelper contient déjà :

- `skills/hi-there/SKILL.md`
- `tools/hi-there.py`
- `commands/hi-there.md`
- `.gitignore`
- `README.md`

On enrichit le Skill et le script Python existants.

## Architecture

Approche retenue : **Skill conversationnel avec état persistant en cache JSON**.

- Le Skill lit/écrit un fichier d’état `~/.cache/powerhelper/hi-there-game.json`.
- Le script Python `tools/hi-there.py` expose trois sous-commandes : `dashboard`, `check-answer`, `set-phrase`.
- Le Skill décide quelle sous-commande appeler en fonction de la phase stockée.
- Le hall of fame est stocké dans `.data/hall-of-fame.md` (gitignoré).

## Fichiers touchés

| Fichier | Changement |
| --- | --- |
| `tools/hi-there.py` | Ajout des sous-commandes et de la logique de jeu, état, hall of fame. |
| `skills/hi-there/SKILL.md` | Mise à jour du `whenToUse` et du body pour piloter les phases. |
| `commands/hi-there.md` | Mise à jour pour lancer le dashboard + la phase de jeu. |
| `.gitignore` | Ajout du dossier `.data/`. |
| `README.md` | Documentation du mini-jeu. |

## Structure de l’état du jeu

Fichier `~/.cache/powerhelper/hi-there-game.json` :

```json
{
  "phase": "ask_yesterday",
  "yesterdays_phrase": "the early bird catches the worm",
  "tomorrows_phrase": null,
  "streak": 2,
  "last_played": "2026-07-09"
}
```

Phases possibles :

- `ask_yesterday` — afficher le dashboard + demander « What was yesterday’s phrase? ».
- `awaiting_yesterday_answer` — vérifier la réponse de l’utilisateur.
- `ask_tomorrow` — demander « What will tomorrow’s phrase be? ».
- `awaiting_tomorrow_phrase` — stocker la phrase de demain et mettre à jour le hall of fame.

## Flow du jeu

### Premier jour

- Aucune `yesterdays_phrase` n’existe.
- Le Skill explique le jeu en anglais.
- Il demande directement : « What will tomorrow’s phrase be? ».
- La réponse est stockée comme `tomorrows_phrase` et deviendra `yesterdays_phrase` le jour suivant.

### Jours suivants

1. L’utilisateur déclenche le Skill (par exemple « good morning »).
2. Phase `ask_yesterday` : le dashboard s’affiche + la question « What was yesterday’s phrase? ».
3. L’utilisateur répond avec une phrase.
4. Phase `awaiting_yesterday_answer` :
   - Si correct : message de félicitations, `streak += 1`, bonus affiché.
   - Si faux : message d’encouragement, `streak = 0`.
5. Phase `ask_tomorrow` : demander « What will tomorrow’s phrase be? ».
6. L’utilisateur répond.
7. Phase `awaiting_tomorrow_phrase` :
   - Stocker la nouvelle phrase.
   - Mettre à jour `.data/hall-of-fame.md`.
   - Afficher un résumé et la phrase de demain confirmée.
8. Réinitialisation à `ask_yesterday` pour le prochain jour.

### Transition jour suivant

Lors d’une nouvelle invocation, si `last_played` est différent de la date du jour, `tomorrows_phrase` est déplacée dans `yesterdays_phrase` et la phase devient `ask_yesterday`.

## Hall of Fame

Fichier `.data/hall-of-fame.md` dans le repo, gitignoré. Format :

```markdown
# Hall of Fame

| Date | Phrase | Streak |
| --- | --- | --- |
| 2026-07-09 | the early bird catches the worm | 3 |
```

## Sous-commandes Python

- `python3 tools/hi-there.py dashboard [location]` — affiche le dashboard météo/news/meme.
- `python3 tools/hi-there.py check-answer "<phrase>"` — vérifie la phrase d’hier.
- `python3 tools/hi-there.py set-phrase "<phrase>"` — stocke la phrase de demain et met à jour le hall of fame.

## Mise à jour du Skill

Le `whenToUse` doit couvrir :

- salutations (« good morning », « hi-there », etc.) ;
- réponses à la question d’hier ;
- réponses à la question de demain.

Le body du Skill lit l’état et appelle la sous-commande appropriée via Bash.

## Error handling

- État corrompu : réinitialiser et expliquer le jeu comme au premier jour.
- Réponse vide : redemander poliment.
- Phrase déjà existante : accepter, mais informer l’utilisateur.

## Testing

- Exécuter `python3 tools/hi-there.py dashboard`.
- Exécuter `python3 tools/hi-there.py set-phrase "test phrase"`.
- Exécuter `python3 tools/hi-there.py check-answer "test phrase"`.
- Vérifier `~/.cache/powerhelper/hi-there-game.json`.
- Vérifier `.data/hall-of-fame.md`.
- Tester dans Kimi Code CLI : « good morning », réponse, phrase de demain.
