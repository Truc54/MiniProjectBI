"""Source/SQL contract from Dung branch commit 84081c0 (sqlserver/ddl, 2026-10-22)."""

from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal, InvalidOperation
import re


class QualityError(ValueError):
    def __init__(self, message, rejected=0):
        super().__init__(message)
        self.rejected = rejected


@dataclass(frozen=True)
class Column:
    kind: str = 'text'
    nullable: bool = True
    size: int = 500
    scale: int = 0
    minimum: object = None

    def parse(self, value, label):
        if value is None:
            if not self.nullable:
                raise QualityError(f'{label}: NULL is not allowed')
            return None
        if not isinstance(value, str):
            raise QualityError(f'{label}: expected source text')
        try:
            if self.kind == 'text':
                if len(value.encode('utf-16-le')) // 2 > self.size:
                    raise ValueError('text exceeds SQL NVARCHAR length')
                return value
            if self.kind == 'int':
                if not re.fullmatch(r'[+-]?[0-9]+', value):
                    raise ValueError('expected integer')
                parsed = int(value)
                if not -(2**31) <= parsed < 2**31:
                    raise ValueError('outside SQL INT range')
            elif self.kind == 'decimal':
                parsed = Decimal(value)
                if not parsed.is_finite():
                    raise ValueError('non-finite number')
                unit = Decimal(10) ** -self.scale
                if parsed != parsed.quantize(unit) or abs(parsed) >= 10 ** (self.size - self.scale):
                    raise ValueError('outside SQL DECIMAL precision/scale')
            elif self.kind == 'date':
                if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
                    raise ValueError('expected YYYY-MM-DD')
                return date.fromisoformat(value)
            elif self.kind == 'time':
                if not re.fullmatch(r'[0-9]{2}:[0-9]{2}:[0-9]{2}Z?', value):
                    raise ValueError('expected HH:MM:SS or HH:MM:SSZ (UTC)')
                # Both forms are UTC in this source. SQL TIME(0) has no zone.
                return time.fromisoformat(value.removesuffix('Z'))
            else:
                raise ValueError('unknown column type')
            if self.minimum is not None and parsed < self.minimum:
                raise ValueError('outside allowed domain')
            return parsed
        except (ValueError, InvalidOperation, OverflowError) as exc:
            raise QualityError(f'{label}: invalid {self.kind} ({exc})') from None


def integer(nullable=True, minimum=None):
    return Column('int', nullable, minimum=minimum)


def text(size, nullable=True):
    return Column('text', nullable, size)


@dataclass(frozen=True)
class Table:
    key: str
    columns: dict
    references: tuple = ()


TABLES = {
    'circuits': Table('circuitId', {
        'circuitId': integer(False, 1), 'circuitRef': text(100, False),
        'name': text(200, False), 'location': text(100), 'country': text(100),
        'lat': Column('decimal', size=9, scale=6),
        'lng': Column('decimal', size=9, scale=6), 'alt': integer(), 'url': text(500),
    }),
    'constructors': Table('constructorId', {
        'constructorId': integer(False, 1), 'constructorRef': text(100, False),
        'name': text(200, False), 'nationality': text(100), 'url': text(500),
    }),
    'drivers': Table('driverId', {
        'driverId': integer(False, 1), 'driverRef': text(100, False),
        'number': integer(), 'code': text(10), 'forename': text(100, False),
        'surname': text(100, False), 'dob': Column('date'),
        'nationality': text(100), 'url': text(500),
    }),
    'status': Table('statusId', {'statusId': integer(False, 1), 'status': text(100, False)}),
    'seasons': Table('year', {'year': integer(False, 1), 'url': text(500)}),
    'races': Table('raceId', {
        'raceId': integer(False, 1), 'year': integer(False, 1),
        'round': integer(False, 1), 'circuitId': integer(False, 1),
        'name': text(200, False), 'date': Column('date', False),
        'time': Column('time'), 'url': text(500),
        **{f'{session}_{kind}': Column(kind)
           for session in ('fp1', 'fp2', 'fp3', 'quali', 'sprint')
           for kind in ('date', 'time')},
    }, (('circuitId', 'circuits', 'circuitId'), ('year', 'seasons', 'year'))),
    'results': Table('resultId', {
        'resultId': integer(False, 1), 'raceId': integer(False, 1),
        'driverId': integer(False, 1), 'constructorId': integer(False, 1),
        'number': integer(), 'grid': integer(False, 0), 'position': integer(True, 1),
        'positionText': text(10, False), 'positionOrder': integer(False, 1),
        'points': Column('decimal', False, 6, 2, 0), 'laps': integer(False, 0),
        'time': text(50), 'milliseconds': integer(True, 0),
        'fastestLap': integer(True, 0), 'rank': integer(True, 0),
        'fastestLapTime': text(50),
        'fastestLapSpeed': Column('decimal', True, 7, 3, 0),
        'statusId': integer(False, 1),
    }, (('raceId', 'races', 'raceId'), ('driverId', 'drivers', 'driverId'),
        ('constructorId', 'constructors', 'constructorId'), ('statusId', 'status', 'statusId'))),
}

LINEAGE = ('_source_file', '_batch_key', '_load_mode', '_ingested_at_utc')


def resolve_request(variables):
    """Only whitelisted identifiers may ever reach generated SQL."""
    file_name = variables.get('file_name')
    table = variables.get('table_name') or variables.get('target_table')
    if not file_name:
        file_name = f'{table or "results"}.csv'
    allowed = {f'{name}.csv': name for name in TABLES}
    if file_name not in allowed:
        raise QualityError('file_name must be a whitelisted core CSV filename (no paths)')
    table = allowed[file_name]
    for alias in ('table_name', 'target_table'):
        if variables.get(alias, table) != table:
            raise QualityError(f'{alias} must match {file_name}')
    if variables.get('schema_name', 'stg') != 'stg':
        raise QualityError('schema_name must be stg')
    mode = variables.get('load_mode', 'full')
    if mode not in ('full', 'incremental'):
        raise QualityError('load_mode must be full or incremental')
    bounds = {}
    for name in ('key_min', 'key_max'):
        value = variables.get(name)
        bounds[name] = None if value is None else integer(False).parse(str(value), name)
    if mode == 'full' and any(v is not None for v in bounds.values()):
        raise QualityError('full load cannot use key bounds')
    if mode == 'incremental' and all(v is None for v in bounds.values()):
        raise QualityError('incremental requires key_min and/or key_max (inclusive)')
    if all(v is not None for v in bounds.values()) and bounds['key_min'] > bounds['key_max']:
        raise QualityError('key_min must be <= key_max')
    batch = variables.get('batch_key') or (
        'full' if mode == 'full' else f'keys_{bounds["key_min"]}_{bounds["key_max"]}'
    )
    if not isinstance(batch, str) or not batch.strip() or len(batch.encode('utf-16-le')) // 2 > 100:
        raise QualityError('batch_key must be non-blank text of at most 100 UTF-16 units')
    return dict(file_name=file_name, table_name=table, target_table=table,
                schema_name='stg', load_mode=mode, batch_key=batch, **bounds)
