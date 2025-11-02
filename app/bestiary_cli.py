import argparse
import json
import os

FILE_PATH = 'bestiary.json'
bestiary = {}

def load_bestiary():
    global bestiary
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            bestiary = json.load(f)
    else:
        bestiary = {}

def save_bestiary():
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(bestiary, f, ensure_ascii=False, indent=4)

def add_monster(name, mtype, weakness):
    if name in bestiary:
        print(f"Монстр '{name}' уже есть в бестиарии.")
        return
    bestiary[name] = {"type": mtype, "weakness": weakness}
    save_bestiary()
    print(f"Добавлен монстр '{name}'.")

def remove_monster(name):
    if name in bestiary:
        del bestiary[name]
        save_bestiary()
        print(f"Монстр '{name}' удалён.")
    else:
        print(f"Монстр '{name}' не найден.")

def search_weakness(weakness):
    found = [name for name, data in bestiary.items() if weakness.lower() in data["weakness"].lower()]
    if found:
        print(f"Монстры, уязвимые к '{weakness}':")
        for name in found:
            print(f" - {name} (Тип: {bestiary[name]['type']})")
    else:
        print(f"Монстров, уязвимых к '{weakness}', не найдено.")

def main():
    load_bestiary()

    parser = argparse.ArgumentParser(description="Управление бестиарием монстров")
    subparsers = parser.add_subparsers(dest="command")

    parser_add = subparsers.add_parser('add', help='Добавить монстра')
    parser_add.add_argument('name', help='Имя монстра')
    parser_add.add_argument('type', help='Тип монстра')
    parser_add.add_argument('weakness', help='Слабость монстра')

    parser_remove = subparsers.add_parser('remove', help='Удалить монстра по имени')
    parser_remove.add_argument('name', help='Имя монстра')

    parser_search = subparsers.add_parser('search', help='Поиск монстров по слабости')
    parser_search.add_argument('weakness', choices=['серебро', 'игни'], help='Искомая слабость')

    args = parser.parse_args()

    if args.command == 'add':
        add_monster(args.name, args.type, args.weakness)
    elif args.command == 'remove':
        remove_monster(args.name)
    elif args.command == 'search':
        search_weakness(args.weakness)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
