"""Core game logic for Dungeon Arena."""

import random

import tcod
from tools.dungeon.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    MONSTERS,
    TILE_FLOOR,
    TILE_WALL,
    WAVE_INTERVAL,
)


class Entity:
    def __init__(
        self,
        x: int,
        y: int,
        glyph: str,
        color,
        name: str,
        hp: int,
        atk: int,
        defense: int,
        xp: int,
    ):
        self.x = x
        self.y = y
        self.glyph = glyph
        self.color = color
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.defense = defense
        self.xp = xp

    def take_damage(self, amount: int) -> None:
        self.hp -= max(0, amount - self.defense)
        if self.hp < 0:
            self.hp = 0


def make_dungeon() -> list[list[int]]:
    """Create a single room with walls around."""
    dungeon = [[TILE_WALL for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    for y in range(1, MAP_HEIGHT - 1):
        for x in range(1, MAP_WIDTH - 1):
            dungeon[y][x] = TILE_FLOOR
    return dungeon


def spawn_monster(wave: int) -> Entity:
    """Spawn a monster near the edges, scaling slightly with wave."""
    choices = ["goblin"] * 5 + ["skeleton"] * 3 + ["orc"] * 2
    if wave >= 3:
        choices += ["orc"] * 2
    if wave >= 5:
        choices += ["skeleton"] * 2
    key = random.choice(choices)
    data = MONSTERS[key]
    edge = random.choice(["top", "bottom", "left", "right"])
    if edge == "top":
        x, y = random.randint(1, MAP_WIDTH - 2), 1
    elif edge == "bottom":
        x, y = random.randint(1, MAP_WIDTH - 2), MAP_HEIGHT - 2
    elif edge == "left":
        x, y = 1, random.randint(1, MAP_HEIGHT - 2)
    else:
        x, y = MAP_WIDTH - 2, random.randint(1, MAP_HEIGHT - 2)
    bonus = wave // 3
    return Entity(
        x,
        y,
        data["glyph"],
        data["color"],
        data["name"],
        data["hp"] + bonus,
        data["atk"] + bonus // 2,
        data["def"] + bonus // 3,
        data["xp"],
    )


def distance(a, b) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def move_towards(
    entity: Entity,
    target_x: int,
    target_y: int,
    dungeon: list[list[int]],
    entities: list,
) -> None:
    dx = target_x - entity.x
    dy = target_y - entity.y
    step_x = max(-1, min(1, dx))
    step_y = max(-1, min(1, dy))
    new_x = entity.x + step_x
    new_y = entity.y + step_y
    if dungeon[new_y][new_x] == TILE_WALL:
        return
    if any(
        e is not entity and e.hp > 0 and e.x == new_x and e.y == new_y
        for e in entities
    ):
        return
    entity.x = new_x
    entity.y = new_y


def attack(attacker: Entity, defender: Entity, messages: list[str]) -> None:
    damage = max(1, attacker.atk - defender.defense)
    defender.take_damage(damage)
    messages.append(f"{attacker.name} hits {defender.name} for {damage}.")
    if defender.hp <= 0:
        messages.append(f"{defender.name} dies!")


def handle_input(
    event,
    player: Entity,
    dungeon: list[list[int]],
    entities: list,
    messages: list[str],
    stats: dict,
) -> bool:
    """Handle one player input. Returns True if a turn was consumed."""
    if event.type != "KEYDOWN":
        return False

    key = event.sym
    dx, dy = 0, 0
    if key in (tcod.event.KeySym.UP, tcod.event.KeySym.K, tcod.event.KeySym.KP_8):
        dy = -1
    elif key in (tcod.event.KeySym.DOWN, tcod.event.KeySym.J, tcod.event.KeySym.KP_2):
        dy = 1
    elif key in (tcod.event.KeySym.LEFT, tcod.event.KeySym.H, tcod.event.KeySym.KP_4):
        dx = -1
    elif key in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.L, tcod.event.KeySym.KP_6):
        dx = 1
    elif key == tcod.event.KeySym.ESCAPE:
        raise SystemExit
    else:
        return False

    target_x = player.x + dx
    target_y = player.y + dy
    if dungeon[target_y][target_x] == TILE_WALL:
        return False

    target = next(
        (e for e in entities if e.hp > 0 and e.x == target_x and e.y == target_y),
        None,
    )
    if target:
        attack(player, target, messages)
    else:
        player.x = target_x
        player.y = target_y
    return True


def run_game(stats: dict):
    """Main game loop. Returns (xp_earned, survived_waves)."""
    dungeon = make_dungeon()
    player = Entity(
        MAP_WIDTH // 2,
        MAP_HEIGHT // 2,
        "@",
        (255, 255, 255),
        "Player",
        20 + (stats["con"] - 10) * 2,
        5 + (stats["str"] - 10) // 2,
        (stats["dex"] - 10) // 3,
        0,
    )
    player.max_hp = player.hp
    entities = [player]
    messages = ["Welcome to Dungeon Arena! Survive the waves."]
    wave = 1
    turn = 0
    spawn_count = 2

    from tools.dungeon.render import setup, render_all

    context, root = setup()

    try:
        while True:
            render_all(context, root, dungeon, entities, player, wave, messages, stats)

            for event in tcod.event.wait():
                if handle_input(event, player, dungeon, entities, messages, stats):
                    turn += 1
                    break

            if turn > 0 and turn % WAVE_INTERVAL == 0:
                wave += 1
                spawn_count = min(spawn_count + 1, 8)
                messages.append(f"Wave {wave} incoming!")
                for _ in range(spawn_count):
                    entities.append(spawn_monster(wave))

            for entity in entities:
                if entity is player or entity.hp <= 0:
                    continue
                if distance(entity, player) == 1:
                    attack(entity, player, messages)
                else:
                    move_towards(entity, player.x, player.y, dungeon, entities)

            if player.hp <= 0:
                messages.append("You died!")
                render_all(context, root, dungeon, entities, player, wave, messages, stats)
                break
    finally:
        context.close()

    xp_earned = sum(e.xp for e in entities if e is not player and e.hp <= 0)
    return xp_earned, wave - 1
