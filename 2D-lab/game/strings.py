"""Texts in Macedonian (default) and English. Press L on the title screen to switch."""

LANG = "mk"

TEXT = {
    "mk": {
        "title": "PERFORATED",
        "subtitle": "Ниво 1: Гордост",
        "press_enter": "Притисни ENTER за почеток",
        "controls": [
            "WASD / стрелки: движење",
            "SHIFT / SPACE: даш (2 полнења)",
            "Пукањето е автоматско",
            "ESC / P: пауза      M: музика      L: јазик",
        ],
        "tagline": "Убивај чувари. Полни го Барот на гордост. Не умирај.",
        "pride": "ГОРДОСТ",
        "stage": "Етапа {n}",
        "stage_desc": {1: "Бавни чувари", 2: "Побрзи групи", 3: "Чувари со копја", 4: "Рој и елитен чувар"},
        "exit_open": "Барот е полн! Оди до портата",
        "upgrade_title": "Превозникот нуди надградба",
        "upgrade_hint": "Избери со 1 / 2 / 3, стрелки + ENTER или клик",
        "paused": "ПАУЗА",
        "pause_help": "ESC / P: продолжи     R: рестарт     Q: излез",
        "game_over": "СЕ РАСТВОРИ",
        "game_over_sub": "Ги изгуби сите срца",
        "victory": "ГОРДОСТА Е ИЗВРШЕНА",
        "victory_sub": "Првиот грев е направен. Чувари се уште те бараат...",
        "retry": "ENTER: обиди се повторно     ESC: излез",
        "again": "ENTER: играј повторно     ESC: излез",
        "kills": "Елиминации",
        "time": "Време",
        "hearts": "Срца",
        "upgrades": {
            "multi": ("Двојни стрели", "+1 стрела по истрел"),
            "rate": ("Брзо пукање", "Пукаш 18% побрзо"),
            "pierce": ("Длабока перфорација", "Стрелите пробиваат +1 непријател"),
            "power": ("Тешки стрели", "+1 штета по стрела"),
            "dash": ("Дополнителен даш", "+1 полнење и побрзо полнење"),
            "speed": ("Лесни нозе", "+10% брзина на движење"),
            "heart": ("Цврсто срце", "+1 макс. срце и лекува 1"),
        },
        "ferryman_line": "„Секој грев има цена. Избери што ќе понесеш.“",
    },
    "en": {
        "title": "PERFORATED",
        "subtitle": "Level 1: Pride",
        "press_enter": "Press ENTER to start",
        "controls": [
            "WASD / arrows: move",
            "SHIFT / SPACE: dash (2 charges)",
            "Shooting is automatic",
            "ESC / P: pause      M: music      L: language",
        ],
        "tagline": "Kill guardians. Fill the Pride bar. Don't die.",
        "pride": "PRIDE",
        "stage": "Stage {n}",
        "stage_desc": {1: "Slow guardians", 2: "Faster groups", 3: "Spear guardians", 4: "Swarm and elite"},
        "exit_open": "The bar is full! Head to the gate",
        "upgrade_title": "The Ferryman offers an upgrade",
        "upgrade_hint": "Pick with 1 / 2 / 3, arrows + ENTER or click",
        "paused": "PAUSED",
        "pause_help": "ESC / P: resume     R: restart     Q: quit",
        "game_over": "YOU DISSOLVED",
        "game_over_sub": "You lost all your hearts",
        "victory": "PRIDE COMMITTED",
        "victory_sub": "The first sin is done. The guardians are still looking for you...",
        "retry": "ENTER: try again     ESC: quit",
        "again": "ENTER: play again     ESC: quit",
        "kills": "Kills",
        "time": "Time",
        "hearts": "Hearts",
        "upgrades": {
            "multi": ("Twin Needles", "+1 needle per shot"),
            "rate": ("Rapid Fire", "Shoot 18% faster"),
            "pierce": ("Deep Perforation", "Needles pierce +1 enemy"),
            "power": ("Heavy Needles", "+1 damage per needle"),
            "dash": ("Extra Dash", "+1 charge and faster recharge"),
            "speed": ("Light Feet", "+10% move speed"),
            "heart": ("Sturdy Heart", "+1 max heart and heal 1"),
        },
        "ferryman_line": "\"Every sin has a price. Choose what you carry.\"",
    },
}


def t(key):
    return TEXT[LANG][key]


def toggle():
    global LANG
    LANG = "en" if LANG == "mk" else "mk"
