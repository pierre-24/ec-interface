import pathlib
from typing import TextIO, Iterator, List, Optional as TOpt

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
    Optional('prefix'): str,
    Optional('additional'): Or([float], None),
})


class ECInputError(Exception):
    pass


class ECParameters:
    def __init__(
        self,
        ne_zc: float,
        ne_added: float,
        ne_removed: float,
        step: float, prefix: str = 'EC',
        additional: TOpt[List[float]] = None,
    ):
        self.ne_zc = ne_zc
        self.ne_added = ne_added
        self.ne_removed = ne_removed
        self.step = step
        self.prefix = prefix
        self.additional = sorted(set(additional)) if additional is not None else []

    def steps(self) -> Iterator[float]:
        """Give the number of electrons for each steps
        """

        start = self.ne_zc - self.ne_removed
        charges_to_add = self.ne_removed + self.ne_added
        i = 0
        j = 0

        while i * self.step <= charges_to_add:
            current = start + i * self.step

            # yield all additionals before this step
            while j < len(self.additional) and self.additional[j] < current:
                yield self.additional[j]
                j += 1

            # skip if similar to the step
            while j < len(self.additional) and self.additional[j] == current:
                j += 1

            yield current
            i += 1

        # yield remaining additional, if any
        yield from self.additional[j:]

    def directories(self, parent: pathlib.Path) -> Iterator[pathlib.Path]:
        """Yield the directories were the calculation are performed
        """

        for n in self.steps():
            yield parent / '{}_{:.3f}'.format(self.prefix, n)

    def __str__(self):
        return 'NELECT = {{{r}:{n}:{s}}} & {{{n}:{a}:{s}}}{adds}'.format(
            n=self.ne_zc,
            s=self.step,
            r=self.ne_zc - self.ne_removed,
            a=self.ne_zc + self.ne_added,
            adds='' if len(self.additional) == 0 else ' & {{{}}}'.format(','.join(str(x) for x in self.additional))
        )

    @classmethod
    def from_yaml(cls, f: TextIO) -> 'ECParameters':
        data = yaml.load(f, Loader=yaml.Loader)

        try:
            data = SCHEMA_EC_INPUT.validate(data)
        except schema.SchemaError as e:
            raise ECInputError(str(e))

        return cls(**data)
