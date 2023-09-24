import pathlib
from typing import TextIO, Iterator

import schema
from schema import Schema, And, Optional, Or
import yaml

POSITIVE_NUMBER = Or(And(float, lambda n: n >= 0), And(int, lambda n: n >= 0))
POSITIVE_NZ_NUMBER = Or(And(float, lambda n: n > 0), And(int, lambda n: n > 0))


SCHEMA_EC_INPUT = Schema({
    'ne_zc': POSITIVE_NZ_NUMBER,
    'ne_added': POSITIVE_NUMBER,
    'ne_removed': POSITIVE_NUMBER,
    'step': POSITIVE_NZ_NUMBER,
    Optional('prefix'): str
})


class ECInputError(Exception):
    pass


class ECParameters:
    def __init__(self, ne_zc: float, ne_added: float, ne_removed: float, step: float, prefix: str = 'EC'):
        self.ne_zc = ne_zc
        self.ne_added = ne_added
        self.ne_removed = ne_removed
        self.step = step
        self.prefix = prefix

    def steps(self) -> Iterator[float]:
        """Give the number of electrons for each steps
        """

        start = self.ne_zc - self.ne_removed
        charges_to_add = self.ne_removed + self.ne_added
        i = 0

        while i * self.step <= charges_to_add:
            yield start + i * self.step
            i += 1

    def directories(self, parent: pathlib.Path) -> Iterator[pathlib.Path]:
        """Yield the directories were the calculation are performed
        """

        for n in self.steps():
            yield parent / '{}_{:.3f}'.format(self.prefix, n)

    def __str__(self):
        return 'NELECT = {{{:.3f},{:.3f},...,{:.3f},{:.3f},...,{:.3f}}}'.format(
            self.ne_zc - self.ne_removed,
            self.ne_zc - self.ne_removed + self.step,
            self.ne_zc,
            self.ne_zc + self.step,
            self.ne_zc + self.ne_added
        )

    @classmethod
    def from_yaml(cls, f: TextIO) -> 'ECParameters':
        data = yaml.load(f, Loader=yaml.Loader)

        try:
            data = SCHEMA_EC_INPUT.validate(data)
        except schema.SchemaError as e:
            raise ECInputError(str(e))

        return cls(**data)
