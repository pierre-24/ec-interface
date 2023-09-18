import pathlib
from typing import TextIO, Self, Iterator

import schema
from schema import Schema, And
import yaml

POSITIVE_FLOAT = And(float, lambda n: n >= 0)
POSITIVE_NZ_FLOAT = And(float, lambda n: n > 0)


SCHEMA_EC_INPUT = Schema({
    'ne_pzc': POSITIVE_NZ_FLOAT,
    'ne_added': POSITIVE_FLOAT,
    'ne_removed': POSITIVE_FLOAT,
    'step': POSITIVE_NZ_FLOAT,
})


class ECInputError(Exception):
    pass


class ECInput:
    def __init__(self, ne_pzc: float, ne_added: float, ne_removed: float, step: float):
        self.ne_pzc = ne_pzc
        self.ne_added = ne_added
        self.ne_removed = ne_removed
        self.step = step

    def steps(self) -> Iterator[float]:
        """Give the number of electrons for each steps
        """

        i = self.ne_pzc - self.ne_removed
        stop = self.ne_pzc + self.ne_added

        while i <= stop:
            yield i
            i += self.step

    @classmethod
    def from_yaml(cls, f: TextIO) -> Self:
        data = yaml.load(f, Loader=yaml.Loader)

        try:
            data = SCHEMA_EC_INPUT.validate(data)
        except schema.SchemaError as e:
            raise ECInputError(str(e))

        return cls(**data)

    def create_directories(
            self,
            incar_file: pathlib.Path,
            poscar_file: pathlib.Path,
            potcar_file: pathlib.Path,
            kpoints_file: pathlib.Path
    ):
        """Create directories containing input files, ready to compute
        """

        def assert_exists(p: pathlib.Path):
            if not p.exists():
                raise ECInputError('`{}` does not exists'.format(p))

        assert_exists(incar_file)
        assert_exists(poscar_file)
        assert_exists(potcar_file)
        assert_exists(kpoints_file)



