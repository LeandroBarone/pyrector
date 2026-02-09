import math
import random
from abc import ABC


class WithUid(ABC):
    NOUNS = (
        'wolf', 'sparrow', 'willow', 'bread', 'anchor', 'storm', 'valley', 'lock',
        'drum', 'lily', 'honey', 'cliff', 'comet', 'vine', 'pearl', 'beetle',
    )
    ADJECTIVES = (
        'bold', 'swift', 'pale', 'vast', 'cold', 'purple', 'dull', 'distant',
        'bright', 'silent', 'rough', 'calm', 'sharp', 'mild', 'hollow', 'steep',
    )
    KNOWN_SUBCLASSES = []
    CLASS_COUNTERS = {}

    def __init__(self):
        self.uid = self.get_uid()

    @classmethod
    def get_next_id_num(cls) -> int:
        if not WithUid.KNOWN_SUBCLASSES:
            WithUid.KNOWN_SUBCLASSES.extend(WithUid.get_subclasses())
        if cls not in WithUid.KNOWN_SUBCLASSES:
            WithUid.KNOWN_SUBCLASSES.append(cls)
        if str(cls) not in WithUid.CLASS_COUNTERS:
            WithUid.CLASS_COUNTERS[str(cls)] = 0
        WithUid.CLASS_COUNTERS[str(cls)] += 1
        return WithUid.CLASS_COUNTERS[str(cls)]

    @classmethod
    def get_subclasses(cls) -> list[type]:
        return [
            subclass for own_subclasses in cls.__subclasses__()
            for subclass in own_subclasses.get_subclasses()
        ] + [cls]

    @classmethod
    def get_uid(cls) -> str:
        id_num = cls.get_next_id_num()
        class_index = WithUid.KNOWN_SUBCLASSES.index(cls)
        code_name = WithUid.uid_to_codename(id_num, class_index)
        return f'{cls.__name__}{id_num}_{code_name}'

    @staticmethod
    def uid_to_codename(id_num: int, class_index: int) -> str:
        total_combinations = len(WithUid.NOUNS) * len(WithUid.ADJECTIVES)

        if id_num < total_combinations:
            return WithUid.codename_from_id_num(id_num, class_index)

        iterations = []
        n = id_num
        while n > 0:
            iterations.append(n % total_combinations)
            n = n // total_combinations
        return ''.join(WithUid.codename_from_id_num(id_num, class_index) for id_num in reversed(iterations))

    @staticmethod
    def codename_from_id_num(id_num: int, seed: int) -> str:
        total_combinations = len(WithUid.NOUNS) * len(WithUid.ADJECTIVES)
        id_num = id_num % total_combinations
        rng = random.Random(seed)
        offset = rng.randint(0, total_combinations - 1)
        mult = rng.randint(1, total_combinations * 2)
        while math.gcd(mult, total_combinations) != 1:
            mult += 1

        final_id_num = (id_num * mult + offset) % total_combinations
        noun = WithUid.NOUNS[final_id_num % len(WithUid.NOUNS)]
        adj = WithUid.ADJECTIVES[final_id_num // len(WithUid.NOUNS) % len(WithUid.ADJECTIVES)]

        return adj.capitalize() + noun.capitalize()
