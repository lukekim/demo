import math
import json
import dataclasses
from typing import Any
import numpy as np
from spec import Report, ReportItem, InferencePoint, InferenceResponse

class NamedFile:
    def __init__(self, name, f):
        self.name = name
        self.f = f

    def __getattr__(self, name: str) -> Any:
        return getattr(self.f, name)

def mse(x):
    return x["mse"]

def mae(x):
    return x["mae"]

def _sanitize(o):
    if isinstance(o, np.ndarray):
        return _sanitize(o.tolist())
    if dataclasses.is_dataclass(o):
        return _sanitize(dataclasses.asdict(o))
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items() if v is not None}
    if isinstance(o, list):
        return list(map(_sanitize, o))
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o

def serialize_report(report: Report | ReportItem) -> str:
    # could do this with a json encoder, but we want some specific behaviour (eg. no null values in maps)
    # that's easier/clearer to just process ourselves
    return json.dumps(_sanitize(report))

def make_inference_response(predicted: np.ndarray, now: float) -> InferenceResponse:
    forecast = []
    print('forecast',)
    for npvalue in predicted:
        # TODO(tim) better *configurable* timestamp extrapolation
        # NB. current models are block based, so time is dense, no extrapolation required
        now += 1
        value = float(npvalue)
        print(f' {value} ({npvalue})',)
        if math.isnan(value):
            value = -1e10
        forecast.append(InferencePoint(now, value, None))

    print("done\n")
    return InferenceResponse(
        forecast=forecast,
    )

