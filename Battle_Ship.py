from itertools import product
import random

SHIP_ALIVE = 0x2588  # закрашенный квадрат █ - живой блок корабля
SHIP_HITTED = 0x2591  # полупрозрачный квадрат ░ - подбитый блок корабля
SPACE = 0x0020  # пробел " " - пустая клетка
MISS = 0x002A  #  * - промах

# класс описание точки
class Dot:

    # границы значений
    leters = [char for char in "ABCDEF"]
    digits = list(range(1, 7))

    def __init__(self, pos) -> None:
        if isinstance(pos, str):
            self.__set_pos_from_str(pos)
        elif isinstance(pos, tuple):
            self.__set_pos_from_tuple(pos)
        else:
            raise ValueError("Неизвестный тип, должен быть tuple или string.")
        self.char = chr(SPACE)

    def __str__(self) -> str:
        # возвращаем точку в виде строки вида A1, B4 ...
        return Dot.leters[self.x] + str(self.y + 1)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, __o: object) -> bool:
        # точки равны если их координаты равны
        return self.x == __o.x and self.y == __o.y

    def __hash__(self):
        return hash(self.__str__())

    def __set_pos_from_str(self, pos: str) -> None:

        if len(pos) != 2:
            raise ValueError("Позиция должна быть описана 2 символами: A5, C7 etc.")

        if pos[0].upper() not in Dot.leters:
            raise ValueError("Первая координата должна быть буквой от A до F: [A...F].")
        else:
            self.x = Dot.leters.index(pos[0].upper())

        if not pos[1].isdigit() or int(pos[1]) not in Dot.digits:
            raise ValueError("Вторая координата должны быть цифрой от 1 до 6: [1...6].")
        else:
            self.y = int(pos[1]) - 1

    def __set_pos_from_tuple(self, pos: str) -> None:

        if len(pos) != 2:
            raise ValueError("Позиция должна быть кортежем с 2 цифрами: (0, 3) or (4, 1) etc.")

        if not isinstance(pos[0], int) or pos[0] + 1 not in Dot.digits:
            raise ValueError("Первая координата должна быть числом от 0 до 5: [0...5].")
        else:
            self.x = pos[0]

        if not isinstance(pos[1], int) or pos[1] + 1 not in Dot.digits:
            raise ValueError("Вторая координата должна быть числом от 0 до 5: [0...5].")
        else:
            self.y = pos[1]

    @staticmethod
    def get_all_dots() -> list:

        dots = product(Dot.leters, Dot.digits)
        return list(map(lambda dot: Dot(dot[0] + str(dot[1])), dots))


class Ship:
    """класс представления корабля"""

    # ориентация: вертикальная или горизонтальная
    directions = ["v", "h"]

    def __init__(self, start_dot: Dot, direction: str, length: int) -> None:

        self.start_dot = start_dot

        # проверка направления
        if direction not in Ship.directions:
            raise ValueError(f"Available direction is: {' or '.join(Ship.directions)}.")
        else:
            self.direction = direction

        # проверка длины
        if length < 1 or length > 3:
            raise ValueError("Длина корабля должна быть от 1 до 3")
        else:
            # число жизней (попадание), в начале равно длине корабля
            self.lives = length
            self.length = length

        # проверяем, влезет ли в поле корабль вертикально
        if direction == Ship.directions[0]:
            try:
                _ = Dot((self.start_dot.x, self.start_dot.y + length - 1))
            except:
                raise ValueError("Корабль не влезает на доску, слишком длинный.")
        # влезет ли в поле корабли горизонтально
        elif direction == Ship.directions[1]:
            try:
                _ = Dot((self.start_dot.x + length - 1, self.start_dot.y))
            except:
                raise ValueError("Корабль не влезает на доску, слишком длинный.")

    def get_dots(self, with_border: bool = False) -> list:

        if self.direction == Ship.directions[0] and not with_border:
            return [Dot((self.start_dot.x, self.start_dot.y + i)) for i in range(self.length)]
        elif self.direction == Ship.directions[1] and not with_border:
            return [Dot((self.start_dot.x + i, self.start_dot.y)) for i in range(self.length)]

        # если нужно вернуть корабль + границу, то сначала получаем точки корабля, рекурсивным вызовом
        ship_dots = self.get_dots()
        dots_and_border = set(ship_dots.copy())
        # затем для каждой точки корабля берем квадрат 3х3 вокруг него
        for ship_dot in ship_dots:
            for dot in product(range(ship_dot.x - 1, ship_dot.x + 2), range(ship_dot.y - 1, ship_dot.y + 2)):
                # валидация точки происходит при ее создании, все невозможные точки просто пропускаем
                try:
                    dots_and_border.add(Dot(dot))
                except:
                    pass
        return list(dots_and_border)

class Field:
    """класс представления поля"""

    def __init__(self, hidden: bool = False) -> None:
        # создание экземпляра поля

        # делаем 2d массив точек
        self.board = [[Dot((x, y)) for x in range(len(Dot.digits))] for y in range(len(Dot.leters))]
        self.ship_list = []
        self.hidden = hidden
        # использованные точки
        self.hitted_dots = set()
        # точки кораблей
        self.ships_dots = set()

    def add_ship(self, ship: Ship) -> None:
        # добавляем корабль на поле

        self.ship_list.append(ship)
        # меняем все точки отрисовки корабля на закрашенный квадрат
        for dot in ship.get_dots():
            if not self.hidden:
                self.board[dot.x][dot.y].char = chr(SHIP_ALIVE)
            self.ships_dots.add(dot)

    def __generate(self, ships_count: list) -> None:
        # Генерация поля

        all_dots_set = set(Dot.get_all_dots())
        for ship_length in ships_count:
            counter = 0
            # для каждого корабля пробуем создать в цикле
            while True:
                counter += 1
                try:
                    # берем рандомную точку как начало корабля, рандомное направление
                    start_dot = random.choice(tuple(all_dots_set))
                    direction = random.choice(Ship.directions)
                    ship = Ship(
                        start_dot=start_dot,
                        direction=direction,
                        length=ship_length,
                    )
                except:
                    # если создать не получилось, повторяем процесс
                    pass
                else:
                    # если создать получилось, проверяем, что нет пересечения
                    # с остальными кораблями, если все ок - выходим из цикла
                    if len(set(ship.get_dots(with_border=True)) - all_dots_set) == 0:
                        break
                if counter >= 2000:
                    raise RuntimeError("Не можем сгенерировать доску")
            self.add_ship(ship)
            all_dots_set = all_dots_set - set(ship.get_dots())

    def generate(self, ships_count: list = [3, 2, 2, 1, 1, 1, 1]) -> None:
        # генерация поля

        # пробуем создать поле пока не получится
        while True:
            try:
                self.__generate(ships_count)
            except:
                # если сюда попали, значит попыток создания было очень много, поэтому реинициализируем поле
                self.__init__(self.hidden)
            else:
                break

    def __mass_mark(self, dot_list: list, marker) -> None:
        # замена символа отображения точки
        for dot in dot_list:
            self.board[dot.x][dot.y].char = marker
        pass

    def shot(self, dot: Dot) -> bool:

        # можно ли стрелять в точку или нет
        if dot in self.hitted_dots:
            raise ValueError("Сюда уже стреляли, выбери другую клетку")
        else:
            self.hitted_dots.add(dot)

        # если не попали помечаем точку промахом и выходим из функции
        if dot not in self.ships_dots:
            self.board[dot.x][dot.y].char = chr(MISS)
            return False

        # если попали
        self.board[dot.x][dot.y].char = chr(SHIP_HITTED)
        for indx, ship in enumerate(self.ship_list):
            if dot in ship.get_dots():
                # уменьшаем жизнь корабля на 1
                ship.lives -= 1
                # если корабль потоплен
                if ship.lives == 0:
                    # получаем границу вокруг корабля
                    border = set(ship.get_dots(with_border=True)) - set(ship.get_dots())
                    # и маркируем границу как промахи, что бы туда нельзя было стрелять
                    self.__mass_mark(list(border), chr(MISS))
                    self.hitted_dots = self.hitted_dots.union(border)
                    self.ship_list.pop(indx)
                    break
        return True


class Board:
    """игровая доска"""

    def __init__(self, player, bot) -> None:
        # доска состоит из двух полей:

        self.player = player
        self.bot = bot
        # список точек куда можно стрелять компьютеру, с самого начала это все точки поля
        self.bot_next_dots = Dot.get_all_dots()
        # список точек куда стрелять в первую очередь. при попадании компьютер будет
        # заносить сюда соседние точки, что бы в первую очередь по ним стрелять
        self.bot_next_turn = []

    def __str__(self) -> str:
        result = "\n" + " " * 11 + "Игрок" + " " * 13 + "Бот" + "\n\n"
        result += ("        " + " ".join(map(str, Dot.digits))) * 2 + "\n"
        result += " " + ("      " + "--" * len(Dot.digits) + "-") * 2 + "\n"
        for indx, (row1, row2) in enumerate(zip(self.player.board, self.bot.board)):
            result += f"     {Dot.leters[indx]} |"
            for cell in row1:
                result += str(cell.char) + "|"
            result += f"    {Dot.leters[indx]} |"
            for cell in row2:
                result += str(cell.char) + "|"
            result += "\n " + ("      " + "--" * len(Dot.digits) + "-") * 2 + "\n"
        return result

    def __player_turn(self) -> bool:
        # вводим точку с клавиатуры
        point = input("Очередь игрока, напечатайте координаты выбранной ячейки (A1, B4, D5 etc): ")
        # пробуем создать точку, при этом проверяются условия, если какая-то ошибка, выводим ее
        # и пользователь повторяет ввод другой точкой
        try:
            dot = Dot(point)
        except Exception as e:
            print(self)
            print(e)
            return False
        # стреляем по полю, если ошибка - выводим ее и пользователь повторяет ввод другой точкой
        try:
            self.bot.shot(dot)
        except Exception as e:
            print(self)
            print(e)
            return False
        print(self)
        return True

    def __bot_turn(self) -> Dot:

        # если до этого подбили корабль и есть точки, куда стрелять в первую
        # очередь, берем точку
        if len(self.bot_next_turn) != 0:
            dot = self.bot_next_turn.pop()
            self.bot_next_dots.remove(dot)
        # или выбираем из всех возможных
        else:
            random.shuffle(self.bot_next_dots)
            dot = self.bot_next_dots.pop()
        # пробуем стрелять, если ошибка, например в точку уже стреляли или
        # еще что-то, то повторяем ход компьютера
        try:
            shot = self.player.shot(dot)
        except:
            return self.__bot_turn()
        # если попали
        if shot:
            # заполняем лист с точками для стрельбы в первую очередь
            next_coord = [
                (dot.x + 1, dot.y),
                (dot.x - 1, dot.y),
                (dot.x, dot.y + 1),
                (dot.x, dot.y - 1),
            ]
            for coord in next_coord:
                try:
                    next_dot = Dot(coord)
                except:
                    pass
                else:
                    if next_dot not in self.player.hitted_dots:
                        self.bot_next_turn.append(next_dot)
        return dot

    def __check_for_winner(self) -> bool:
        # если у игрока не осталось кораблей, рисуем доску и выходим
        if len(self.player.ship_list) == 0:
            print(self)
            print(" " * 10 + "===> Бот выиграл! <===")
            return True
        # если у компьютера не остальсь кораблей, рисуем доску и выходим
        elif len(self.bot.ship_list) == 0:
            print(self)
            print(" " * 10 + "===> Игрок выиграл! <===")
            return True
        print(self)
        return False

    def run_game(self) -> None:
        """обработка цикла хода"""
        # флаг кто ходит
        player_turn = True
        while True:
            if player_turn:
                turn = self.__player_turn()
                if not turn:
                    continue
                player_turn = not player_turn
            else:
                dot = self.__bot_turn()
                player_turn = not player_turn
                print("=" * 50)
                print(f"Сhoice of bot: {dot}")
            win = self.__check_for_winner()
            if win:
                break


if __name__ == "__main__":
    # создаем два поля: игроку и боту
    player = Field()
    player.generate()
    bot = Field(hidden=True)
    bot.generate()
    # создаем доску с этими двумя полями
    board = Board(player, bot)
    print(board)
    # запускаем игру
    board.run_game()