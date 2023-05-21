from .models import *


def upsertDataPoint(**data):
    return DataPoint.update(**data)