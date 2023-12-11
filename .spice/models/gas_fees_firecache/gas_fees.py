#!/usr/bin/python

import os
from typing import List
import numpy as np
import pandas as pd
import xgboost
import tqdm
from sklearn.metrics import mean_absolute_error
#from ipfs import Ipfs
#from spec import TrainParams, TrainResponse, InferenceParams, InferenceResponse, HtmlReportItem, PlotlyLayout, PlotlyReportItem, Report
#from util import mse, serialize_report, make_inference_response
#from plotly_utils import scatter, chart_test_results, chart_best_worst, generate_train_report


# TODO move to spec.py
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class TrainParams:
    model_id: str
    input_parquet_cid: str
    lookback_size: int
    forecast_size: int
    epochs: int
    metadata: Optional[dict]

@dataclass
class TrainResponse:
    model_weights_name: str
    model_weights_cid: str
    report_cid: str

@dataclass
class InferencePoint:
    timestamp: float
    value: float
    covariate: Optional[float]

@dataclass
class InferenceParams:
    model_id: str
    lookback: list[InferencePoint]
    model_weights_cid: str
    model_weights_name: str
    lookback_size: int
    forecast_size: int
    metadata: Optional[dict] = None

@dataclass
class InferenceResponse:
    forecast: list[InferencePoint]

@dataclass
class PlotlyGrid:
    subplots: any = None
    rows: int = None
    cols: int = None

@dataclass
class PlotlyLayout:
    title: str
    width: int = None
    height: int = None
    grid: PlotlyGrid = None
    yaxis1: any = None
    yaxis2: any = None
    annotations: list = None

@dataclass
class HtmlReportItem:
    type: str = field(default='html', init=False)
    html: str

@dataclass
class PlotlyReportItem:
    type: str = field(default='plotly', init=False)
    traces: List[any]
    layout: PlotlyLayout


ReportItem = HtmlReportItem | PlotlyReportItem

@dataclass
class Report:
    items: list[ReportItem]

# end spec.py


# TODO get from util.py

import math
import json
import dataclasses
from typing import Any
import numpy as np
#from spec import Report, ReportItem, InferencePoint, InferenceResponse

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
# end util.py




def make_xgboost_data(filled_df: pd.DataFrame, lookback_size: int, lookahead_size: int, has_covariate: bool) -> np.array:
    lo = filled_df['ts'].min()
    hi = filled_df['ts'].max()
    print(lo, hi, "=", hi - lo, 'with covariates' if has_covariate else 'without covariates')

    sparse = set(filled_df['ts'].to_numpy())
    pad = []
    for i in range(lo, hi):
        if i not in sparse:
            pad.append(i)

    print(len(pad), 'padded')

    pad_df = pd.DataFrame(data={'ts': pad})
    filled_df = pd.concat([filled_df, pad_df])
    filled_df.sort_values('ts', inplace=True, ignore_index=True)

    filled_df = filled_df.interpolate(method='pad') \
        .replace([np.inf, -np.inf], np.nan) \
        .dropna()

    data = filled_df['y']
    if has_covariate:
        covariates = filled_df['covariate']

    def to_dataset(data: np.array, covariates: np.array, num_lookback: int, num_lookahead: int = 1, dropna: bool = True) -> np.array:
        cols = {}
        for i in range(num_lookback, 0, -1):
            cols[f'back{i}'] = data.shift(i)

        if has_covariate:
            for i in range(num_lookback, 0, -1): # TODO(tim) support different lookback window sizes
                cols[f'corr{i}'] = covariates.shift(i)
        for i in range(0, num_lookahead):
            cols[f'ahead{i}'] = data.shift(-i)

        agg = pd.concat(cols, axis=1)
        if dropna:
            agg.dropna(inplace=True)
        return agg.values

    return to_dataset(data, covariates, lookback_size, lookahead_size)


def has_covariates(metadata: dict | None):
    if not metadata:
        return False
    return bool(metadata.get('covariate'))

def split_train_test(df, num_test, step=1):
    return df[:-num_test:step, :], df[-num_test::step, :]

def xgboost_forecast(train, testx, num_lookahead):
    train = np.asarray(train)
    trainx, trainy = train[:, :-num_lookahead], train[:, -num_lookahead:]
    model = xgboost.XGBRegressor(objective='reg:squarederror', n_estimators=1000)
    model.fit(trainx, trainy)
    yhat = model.predict([testx])
    return yhat[0], model

def walk_forward_analysis(df, num_lookahead, test_step=1):
    predictions = []
    train, test = split_train_test(df, int(0.2 * len(df)), test_step)
    history = list(train)
    model = None
    for i in tqdm.tqdm(range(len(test))):
        testx, testy = test[i, :-num_lookahead], test[i, -num_lookahead]
        yhat, model = xgboost_forecast(history, testx, num_lookahead)
        print(f'{i:4d} > expected={testy:.1f}, predicted={yhat:.1f}')
        predictions.append(yhat)
        history.append(test[i])
    error = mean_absolute_error(test[:, -num_lookahead], predictions)
    return model, error, test[:, -num_lookahead], predictions

#def train(self, all_data: pd.DataFrame, params: TrainParams, ipfs) -> TrainResponse:
def train(context, runtime):
    print("\n\nRUNNING USER XGBOOST TRAIN ACTIVITY\n\n")
    print('context', context)

    print(f'all data @ {os.environ}')
    all_data = pd.read_parquet(os.environ['DATA_DIR'])
    print('training data:', all_data.shape)
    print(all_data.head())
    all_data.sort_values("ts", inplace=True, ignore_index=True)
    metadata = context['metadata']
    has_covariate = has_covariates(metadata)

    ds = make_xgboost_data(all_data, context['lookback_size'], context['forecast_size'], has_covariate)
    wfa_ds = ds[-1000:] # TODO(tim) parameterise better
    print(ds.shape, wfa_ds.shape)
    model, error, y, yhat = walk_forward_analysis(wfa_ds, context['forecast_size'], 10)
    print(f'MAE: {error}')
    print(y)
    print(yhat)

    # logger.info(f"train {len(train_data.inputs)}, test {len(test_data.inputs)}")

    # no need to use runtime, just save weights directly into the output dir!
    model_weights_name = 'model.ubj'
    path = os.path.join(os.environ['OUTPUT_DIR'], model_weights_name)
    model.save_model(path)
    #with open(path, 'rb') as f:
    #    #model_weights_cid = self.ipfs.upload_file(f, model_weights_name)
    #    runtime.upload(f, model_weights_name)
    #print('UPLOADED WEIGHTS:', model_weights_cid)

    test_results = generate_test_results(model, ds, context['forecast_size'], has_covariate)
    report = json.dumps({
      'items': [
        {
          'type': 'html',
          'html': f'<h1>Train Report</h1><div>{len(test_results)} results:</div><ol>' + '\n'.join(list(map(lambda r : f'<li>{json.dumps(r)}</li>', test_results))) + '</ol>',
        }
      ],
    })
    runtime.upload(report, 'report.json')


    #test_chart = chart_test_results(test_results)
    #best_worst_chart = chart_best_worst(test_results)
    #report_items = generate_train_report(test_chart, best_worst_chart).items
    ## report_items.append(HtmlReportItem(f'<div>{stats}</div>'))
    #backtest_report = generate_backtest_report(model, ds, params.forecast_size)
    #report_items.extend(backtest_report.items)
    #report_json = serialize_report(Report(items=report_items))
    #report_cid = self.ipfs.upload_string(report_json)
    #print('uploaded report:', report_cid)

    #print("done\n")
    #return TrainResponse(
    #    model_weights_name=model_weights_name,
    #    model_weights_cid=model_weights_cid,
    #    report_cid=report_cid,
    #)

def infer(context, runtime) -> InferenceResponse:
    print('RUNNING USER XGBOOST INFERENCE ACTIVITY')
    print('context', context)

    lookback_size = context['lookback_size']
    model = xgboost.XGBRegressor(objective='reg:squarederror', n_estimators=1000)
    model.load_model(model_path)
    lookback = pd.DataFrame(context['lookback'])
    metadata = context['metadata']

    input_window = lookback['value'][-lookback_size:].to_numpy().reshape(-1).astype("float32")
    if has_covariates(metadata):
        covariates = lookback['covariate'][-lookback_size:].to_numpy().reshape(-1).astype("float32")
        input_window = np.concatenate([input_window, covariates], axis=None)
    print('input shape', input_window.shape)
    predicted = model.predict(input_window.reshape(1, -1))

    now = context['lookback'][-1].timestamp
    return make_inference_response(predicted, now)


# TODO(tim) f1, MSE, MAE, auto-correlation across all train+validation+test sets (ideally measured per-train epoch)
def generate_test_results(model, data: np.array, lookahead_size: int, has_covariate: bool) -> list:
    test_results = []
    i = 0
    num = len(data)
    num = min(num, 1000) # HACK(tim) sample this down for reasonable runtime while we're pre-GPU
    for i in tqdm.tqdm(range(num)):
        input_window = data[i, :-lookahead_size]
        covariates = None

        actual = data[i, -lookahead_size:]
        predicted = model.predict(input_window.reshape(1, -1))

        # pull this out *after* running prediction (which requires lookback+covariates in a flat array)
        if has_covariate:
            i = len(input_window) // 2 # TODO(tim) not true if inputs+covariates are allowed to have different lookbacks
            covariates = input_window[i:]
            input_window = input_window[:i]

        baseline = np.full(predicted.shape, float(input_window[-1]))

        # pylint: disable=R1735
        test_results.append(dict(
            index=i,
            window=input_window,
            covariates=covariates,
            predicted=predicted,
            actual=actual,

            mse=np.sum(np.square(predicted - actual)) / len(predicted),
            mae=np.sum(np.abs(predicted - actual)) / len(predicted),
            mape=np.sum(np.abs((predicted - actual) / (actual + 1e-9))) / len(predicted),

            bmse=np.sum(np.square(baseline - actual)) / len(baseline),
            bmae=np.sum(np.abs(baseline - actual)) / len(baseline),
            bmape=np.sum(np.abs((baseline - actual) / (actual + 1e-9))) / len(baseline),
        ))
        # pylint: enable=R1735

    test_results.sort(key=mse)

    return test_results


def generate_backtest_report(model, df: np.array, lookahead_size: int) -> Report:  # noqa: C901
    num = min(len(df), 10000) # TODO(tim) parameterise this better

    predictions = []
    actuals = df[:, -lookahead_size:].reshape(-1)
    for i in range(0, num):
        in0 = df[i, :-lookahead_size].reshape(1, -1)

        # pylint: disable=E1121
        out0 = model.predict(in0)
        predictions.extend(out0)

    predictions = np.array(predictions).reshape(-1)

    def prepend_na(d):
        return np.concatenate([np.array([np.nan]), d])

    def plot_backtest() -> Report:
        start = 0
        end = len(predictions)

        x = np.arange(start, end)
        baseline = prepend_na(actuals[start:end - 1])

        traces = [
            scatter(x=x, y=actuals[start:end], name='actual', line={'shape': 'hv'}),
            scatter(x=x, y=actuals[start:end] + 1, name='±1 margin', legendgroup='margin',
                    mode='lines', line_color='grey', line={'shape': 'hv'}),
            scatter(x=x, y=actuals[start:end] - 1, name='±1 margin', showlegend=False, legendgroup='margin',
                    mode='lines', line_color='grey', fill='tonexty', line={'shape': 'hv'}),
            scatter(x=x, y=actuals[start:end] * 1.01, name='1% margin', legendgroup='margin2',
                    mode='lines', line_color='lightgrey', line={'shape': 'hv'}),
            scatter(x=x, y=actuals[start:end] / 1.01, name='1% margin', showlegend=False, legendgroup='margin2',
                    mode='lines', line_color='lightgrey', fill='tonexty', line={'shape': 'hv'}),
        ]

        traces.append(scatter(x=x, y=predictions[start:end], name='predicted', line={'shape': 'hv'}))
        traces.append(scatter(x=x, y=baseline, name='baseline', line={'shape': 'hv'}))

        layout = PlotlyLayout(
            title='Backtest',
            height=600,
        )

        return PlotlyReportItem(traces=traces, layout=layout)

    report_items = [plot_backtest()]

    a = actuals[:len(predictions)]
    b = prepend_na(a[:-1])

    def add_table_to_report(text: str, rows: List[str]):
        inner = '\n'.join(rows)
        report_items.append(HtmlReportItem(f'<h3>{text}</h3><table><tr><th>margin</th><th>in bounds</th><th>total</th><th>percent</th></tr>{inner}</table>'))

    def check_add(add, pp=predictions, aa=a):
        bounded = ~((pp > (aa + add)) | (pp < (aa - add)))
        bounded = len(np.argwhere(bounded))
        return f'<tr><td>&plusmn;{add:0.6f}</td><td>{bounded:5d}</td><td>{len(pp)}</td><td>{bounded * 100 / len(pp):3.2f}%</td></tr>'

    def check_mul(mul, pp=predictions, aa=a):
        bounded = ~((pp > (aa * mul)) | (pp < (aa / mul)))
        bounded = len(np.argwhere(bounded))
        return f'<tr><td>{mul:0.6f}x</td><td>{bounded:5d}</td><td>{len(pp)}</td><td>{bounded * 100 / len(pp):3.2f}%</td></tr>'

    add_table_to_report('prediction', [
        check_add(0.1),
        check_add(1),
        check_add(10),

        check_mul(1.1),
        check_mul(1.01),
        check_mul(1.005),
        check_mul(1.001),
        check_mul(1.00001),
        check_mul(1+1e-10),
    ])

    add_table_to_report('baseline', [
        check_add(0.1, b),
        check_add(1, b),
        check_add(10, b),

        check_mul(1.1, b),
        check_mul(1.01, b),
        check_mul(1.005, b),
        check_mul(1.001, b),
        check_mul(1.00001, b),
        check_mul(1+1e-10, b),
    ])

    return Report(items=report_items)

