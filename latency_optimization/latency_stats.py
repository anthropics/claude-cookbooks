"""Statistics, tables, and charts for the latency cookbook's logged sweep. No API calls.

results/sweep.jsonl and results/race.jsonl hold one line per task attempt that counts. In each file every setting ran
the same tasks in the same rounds, so each comparison is made inside a round and then combined over the rounds."""

import json
import re
from dataclasses import dataclass, fields

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML
from matplotlib.lines import Line2D

PERCENTILES = {"p50": 0.5, "p90": 0.9}
# What a percentile metric is taken of, keyed by the words before "p50" or "p90": (the field, its description).
# "p90" is of seconds per task (the whole task's TTLT), "first token p90" of seconds to the first visible token
WAITS = {
    "": ("secs", "seconds per task"),
    "first token": ("first_token_secs", "seconds to the first visible token"),
}
# Anthropic's chart colors. The models take the first three categorical hues, in order
COLORS = {"opus": "#2a78d6", "sonnet": "#eb6834", "haiku": "#1baf7a"}
INK, SOFT_INK = "#0b0b0b", "#52514e"  # primary and secondary text
GREY, GRID, SURFACE = (
    "#c3c2b7",
    "#e1e0d9",
    "#fcfcfb",
)  # axes and whatever recedes, gridlines, the background
BRAND = {
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.axisbelow": True,  # gridlines are solid, so they go under everything else
    "axes.edgecolor": GREY,
    "axes.labelcolor": SOFT_INK,
    "axes.titlecolor": INK,
    "grid.color": GRID,
    "legend.labelcolor": SOFT_INK,
    "text.color": INK,
    "xtick.color": GREY,
    "xtick.labelcolor": SOFT_INK,
    "ytick.color": GREY,
    "ytick.labelcolor": SOFT_INK,
}
TIE = 1e-9  # figures this close count as equal: accuracy ties are common, and float rounding must not break one


def _text(rows, places=1):
    """Every value as text. A heading that ends in " s" hands the unit to its values: {"done, s": 4.5} reads 4.5s"""
    form = {float: f"{{:.{places}f}}".format, int: "{:,}".format}

    def cell(k, v):
        text = form.get(type(v), str)(v)
        return (k[:-2].rstrip(","), f"{text}s") if k.endswith(" s") else (k, text)

    return [dict(cell(k, v) for k, v in row.items()) for row in rows]


def _aligned(rows):
    """Rows of text as one aligned table: the first column to the left, the rest to the right"""
    wide = {k: max(len(k), *(len(row[k]) for row in rows)) for k in rows[0]}
    first, *rest = wide
    lines = (
        [row[first].ljust(wide[first]), *(row[k].rjust(wide[k]) for k in rest)]
        for row in [{k: k for k in wide}, *rows]
    )
    return "\n".join("   ".join(line).rstrip() for line in lines)


def show(rows, places=1):
    """Print dicts as an aligned table, with floats to `places` decimals and seconds marked on the values"""
    print(_aligned(_text(rows, places)))


class Table(HTML):
    """An HTML table that reads as the same aligned table as show() wherever HTML outputs aren't rendered"""

    def __init__(self, html, text):
        super().__init__(html)
        self.text = text

    def __repr__(self):
        return self.text


def table(rows):
    """The same rows as an HTML table. Values go in unescaped, so they can carry tags such as <b>"""
    rows = _text(rows)
    lines = [
        [f"<th>{k}</th>" for k in rows[0]],
        *([f"<td>{v}</td>" for v in r.values()] for r in rows),
    ]
    html = "<table>" + "".join(f"<tr>{''.join(line)}</tr>" for line in lines) + "</table>"
    untagged = [{k: re.sub(r"</?\w+>", "", v) for k, v in r.items()} for r in rows]
    return Table(html, _aligned(untagged))


def show_task(row, cfg):
    """Shows a row for each model call of a task, then prints its totals. cfg: the setting it ran on, for prices"""
    from IPython.display import display

    calls = [
        {
            "call": f"{row['task']}, call {n}",
            "wait, s": c["secs"],
            "tools called": ", ".join(c["tools"]),
            "input tokens": c["input_tokens"],
            "cache read, tokens": c["cache_read"],
            "cache write, tokens": c["cache_write"],
            "output tokens": c["output_tokens"],
            "of which thinking": c["thinking_tokens"],
        }
        for n, c in enumerate(row["calls"], 1)
    ]
    # Columns ending in "tokens" that are 0 on every call (the cache columns, when a task ran without caching) are left out
    empty = {k for k in calls[0] if k.endswith("tokens") and not any(c[k] for c in calls)}
    display(table([{k: v for k, v in c.items() if k not in empty} for c in calls]))
    secs = sum(c["secs"] for c in row["calls"])
    usd = sum(cfg.dollars(c) for c in row["calls"])
    grade = "correct" if row["correct"] else "wrong"
    print(f"→ {grade}, {secs:.1f}s waiting on the model, ${usd:.3f}\n")


def first_visible_token(line):
    """Seconds from a task's start to its first visible token, the first that isn't thinking (text or a tool call): the
    first call's time to its first token, which counts hidden thinking as a token, plus that thinking, timed at the
    call's own seconds per output token. The log has no mark for where thinking ends, so this is an estimate whenever
    the first call thinks, and the service's own measurement when it doesn't"""
    if "call_first_visible_secs" in line:  # measured directly, where the log has it
        return line["call_first_visible_secs"][0]
    first, secs = line["call_first_token_secs"][0], line["call_secs"][0]
    tokens, thinking = line["call_output_tokens"][0], line["call_thinking_tokens"][0]
    return first + thinking * (secs - first) / tokens if tokens else first


def _wait(metric):
    """(field, quantile) for a percentile metric such as "p90" or "first token p90", or None for a field to average"""
    wait, _, percentile = metric.rpartition(" ")
    return (WAITS[wait][0], PERCENTILES[percentile]) if percentile in PERCENTILES else None


def in_words(metric):
    """A percentile metric in words, as the charts print it. "first token p90" reads "p90 seconds to the first visible token" """
    wait, _, percentile = metric.rpartition(" ")
    return f"{percentile} {WAITS[wait][1]}"


@dataclass(frozen=True)
class Versus:
    """One setting against another: a ratio of seconds, calls, tokens, or dollars, or a difference in points of accuracy"""

    change: float
    lo: float  # lo to hi is the 95% interval
    hi: float
    rounds: tuple  # the same figure in each round
    verdict: str  # "cut", "raised", or "not significant"


class Sweep:
    def __init__(self, path, config, draws=2000, seed=210384, keep=None, stop=None):
        """path: the log, one JSON object per line, or a list of logs read as one. config: the notebook's Config class. One is
        built from the fields of the same names on each line, and its dollars() prices that line's tokens. draws: redraws for
        each interval. keep: if given, only the lines for which keep(line) is true are read. stop: if given, a task that
        ran past this many seconds is scored as the notebook's run_task() leaves one it stops: it took `stop` seconds and
        recorded nothing, so it's wrong. Its calls and tokens stay as logged"""
        self.config = config
        paths = path if isinstance(path, (list, tuple)) else [path]
        lines = [json.loads(line) for p in paths for line in open(p)]
        lines = [line for line in lines if keep is None or keep(line)]
        # Blended figures weight the jobs (the type field) equally, and the levels equally within a job
        levels = sorted({(r["type"], r["level"]) for r in lines})
        types = [kind for kind, _ in levels]
        self.share = {level: 1 / len(set(types)) / types.count(kind) for kind, level in levels}
        self.hardest = tuple(
            max(lv for k, lv in levels if k == kind) for kind in sorted(set(types))
        )
        # Tasks in one cluster (say, two pre-screens at one repair shop) are redrawn together, under the lower level
        stratum = {}
        for r in lines:
            mine = (r["type"], r["level"])
            stratum[r["cluster"]] = min(stratum.get(r["cluster"], mine), mine)
        number = {cluster: i for i, cluster in enumerate(sorted(stratum))}
        self.rounds = sorted({r["round"] for r in lines})
        self.rows, seen = {}, set()
        for r in lines:
            cfg = config(**{f.name: r[f.name] for f in fields(config)})
            assert (cfg, r["round"], r["task"]) not in seen, (
                f"{r['task']} appears twice for {cfg.name} in round {r['round']}. If the log has a field that config "
                "lacks, such as caching, pass a config class that has it"
            )
            seen.add((cfg, r["round"], r["task"]))
            if stop is not None and r["secs"] > stop:
                r |= {"secs": float(stop), "correct": False}
            if "call_first_token_secs" in r:
                r["first_token_secs"] = first_visible_token(r)
            r |= {
                "usd": cfg.dollars(r),
                "calls": len(r["call_secs"]),
                "group": number[r["cluster"]],
            }
            self.rows.setdefault((cfg, r["round"]), []).append(r)
        self.settings = sorted({cfg for cfg, _ in self.rows}, key=lambda cfg: cfg.order)
        # For the 95% intervals the tasks are redrawn with replacement inside each level. One redraw applies to every
        # setting and round at once, which keeps each comparison paired. Row 0 is the tasks as they are
        rng = np.random.default_rng(seed)
        strata = [np.array([number[c] for c in sorted(stratum) if stratum[c] == s]) for s in levels]
        self.draws = np.zeros((1 + draws, len(stratum)))
        self.draws[0] = 1
        for draw in self.draws[1:]:
            for ids in filter(len, strata):
                np.add.at(draw, ids[rng.integers(0, len(ids), len(ids))], 1)
        self._memo = {}

    def pick(self, **want):
        """The settings whose fields match, as in pick(model=OPUS, effort="low")"""
        return [cfg for cfg in self.settings if all(getattr(cfg, f) == v for f, v in want.items())]

    def stat(self, cfg, metric, **only):
        """metric: "p50" or "p90" of seconds per task, "first token p50" or "first token p90" of seconds to the first
        visible token, or a field to average ("correct", "usd", "calls", "output_tokens").
        only: keep some tasks, as in type="quote" or level=sweep.hardest.
        Returns an array of shape (rounds, 1 + redraws), with the tasks as they are in column 0"""
        only = {f: v if isinstance(v, tuple) else (v,) for f, v in only.items()}
        memo = (cfg, metric, tuple(sorted(only.items())))
        if memo not in self._memo:
            out = []
            for rnd in self.rounds:
                rows = [r for r in self.rows[(cfg, rnd)] if all(r[f] in v for f, v in only.items())]
                assert rows, f"no task of {cfg.name} in round {rnd} matches {only}"
                w = self.draws[:, [r["group"] for r in rows]]
                level = np.array([r["level"] for r in rows])
                # Each level keeps its share of the weight, whatever was redrawn or left out
                for lv in np.unique(level):
                    total = w[:, level == lv].sum(axis=1, keepdims=True)
                    w[:, level == lv] *= self.share[lv] / np.where(total > 0, total, 1)
                total = w.sum(axis=1)
                # A redraw that holds none of the tasks `only` keeps divides 0 by 0, and its figure is NaN
                with np.errstate(invalid="ignore"):
                    # The weighted percentile: sort by seconds, take the first task where the running weight reaches it
                    if _wait(metric):
                        field, quantile = _wait(metric)
                        assert all(field in r for r in rows), (
                            f"the log has no call_first_token_secs for {cfg.name}"
                        )
                        order = np.argsort([r[field] for r in rows], kind="stable")
                        reached = (
                            np.cumsum(w[:, order], axis=1) / total[:, None] >= quantile - 1e-12
                        )
                        secs = np.array([r[field] for r in rows])[order][reached.argmax(axis=1)]
                        out.append(np.where(total > 0, secs, np.nan))
                    else:
                        out.append(w @ np.array([r[metric] for r in rows], float) / total)
            self._memo[memo] = np.array(out)
        return self._memo[memo]

    def value(self, cfg, metric, **only):
        """stat() on the tasks as they are, averaged over the rounds"""
        return float(self.stat(cfg, metric, **only)[:, 0].mean())

    def versus(self, cfg, base, metric="p50"):
        """cfg against base. Seconds, counts, and dollars give a ratio, the geometric mean of the rounds' ratios. It is
        "cut" or "raised" when its 95% interval excludes 1 and every round falls on that side, given at least three
        rounds. metric="correct" gives a difference in points, judged on its interval alone"""
        a, b = self.stat(cfg, metric), self.stat(base, metric)
        if metric == "correct":
            each, null = 100 * (a - b), 0
            pooled, below, above = each.mean(axis=0), True, True
        else:
            each, null = a / b, 1
            pooled, enough = np.exp(np.log(each).mean(axis=0)), len(self.rounds) >= 3
            below = enough and (each[:, 0] < 1 - TIE).all()
            above = enough and (each[:, 0] > 1 + TIE).all()
        lo, hi = np.percentile(pooled[1:], [2.5, 97.5])
        cut, raised = below and hi < null - TIE, above and lo > null + TIE
        verdict = "cut" if cut else "raised" if raised else "not significant"
        return Versus(float(pooled[0]), float(lo), float(hi), tuple(each[:, 0]), verdict)

    def fit(self, cfg, rounds=None):
        """A straight line through every model call of the setting: seconds = a + b * output tokens.
        Returns (a, 100 * b): fixed seconds per call, and seconds per 100 output tokens. rounds: all, unless given"""
        rows = [r for rnd in rounds or self.rounds for r in self.rows[(cfg, rnd)]]
        tokens = np.concatenate([r["call_output_tokens"] for r in rows])
        b, a = np.polyfit(tokens, np.concatenate([r["call_secs"] for r in rows]), 1)
        return float(a), float(100 * b)

    def frontier(self, settings, metric="p50"):
        """Fastest first, the settings that are more accurate than every faster one"""
        front = []
        for cfg in sorted(
            settings, key=lambda c: (self.value(c, metric), -self.value(c, "correct"))
        ):
            if not front or self.value(cfg, "correct") > self.value(front[-1], "correct") + TIE:
                front.append(cfg)
        return front

    def against(self, cfg, base, metric, form="×{:.2f} ({:.2f} to {:.2f})"):
        """cfg's change against base with its 95% interval, in bold if it was cut or raised"""
        v = self.versus(cfg, base, metric)
        text = form.format(v.change, v.lo, v.hi).replace("-0.0", "+0.0")
        return "" if cfg == base else text if v.verdict == "not significant" else f"<b>{text}</b>"

    def result_row(self, cfg, base, versus="first row", rounds=False, waits=("p50", "p90")):
        """One row of a results table: cfg's own figures, and its changes against base. versus: what the headings call
        base. waits: the percentile metrics to show, such as "p50" or "first token p90". rounds=True adds each round's own
        ratio for each"""
        points = self.against(cfg, base, "correct", "{:+.1f} ({:+.1f} to {:+.1f})")
        row = {"setting": cfg.name, "correct": f"{self.value(cfg, 'correct'):.1%}"}
        row[f"correct vs {versus}, points"] = points
        for metric in waits:
            seconds = self.value(cfg, metric)
            # As in rank_row(): waits for a first token get a second decimal place
            row[f"{metric} s"] = seconds if _wait(metric)[0] == "secs" else f"{seconds:.2f}"
            row[f"{metric} vs {versus}"] = self.against(cfg, base, metric)
            if rounds:
                each = self.versus(cfg, base, metric).rounds if cfg != base else ()
                row[f"{metric} ratio in each round"] = " ".join(f"{x:.2f}" for x in each)
        row["calls / task"] = self.value(cfg, "calls")
        row["output tokens / task"] = round(self.value(cfg, "output_tokens"))
        row["$ / task"] = f"${self.value(cfg, 'usd'):.4f}"
        return row

    def results_table(self, settings, base=None, rounds=False, waits=("p50", "p90")):
        """A table with base in the first row (the baseline, Config(), unless given), then one row for each setting,
        compared with base. Columns that are blank in every row are left out, as the comparisons are for base alone"""
        base = base or self.config()
        rest = [cfg for cfg in settings if cfg != base]
        rows = [self.result_row(cfg, base, rounds=rounds, waits=waits) for cfg in [base, *rest]]
        return table(
            [{k: v for k, v in row.items() if any(r[k] != "" for r in rows)} for row in rows]
        )


def to_beat(sweep, cfg, products):
    """A row per product: cfg's p50 and p90 of the wait that product is judged on. products: {name: its metric,
    as in "first token p90"}"""
    rows = []
    for name, metric in products.items():
        wait, _, percentile = metric.rpartition(" ")
        places = 2 if wait else 1
        row = {"product": name, "wait": WAITS[wait][1]}
        row |= {p: f"{sweep.value(cfg, f'{wait} {p}'.strip()):.{places}f}s" for p in PERCENTILES}
        rows.append(row | {"optimizes for": percentile})
    return table(rows)


def rank_row(sweep, cfg, bounds, tied=""):
    """One line of a product's ranking: the product's own metric first, then seconds per task.
    Hardest level: accuracy on each job's hardest level, weighted equally"""
    hardest = np.mean([sweep.value(cfg, "correct", level=level) for level in sweep.hardest])
    row = {
        "setting": cfg.name,
        "correct (hardest level)": f"{sweep.value(cfg, 'correct'):.1%} ({hardest:.1%})",
    }
    for metric in dict.fromkeys((bounds.metric, "p50", "p90")):
        seconds = sweep.value(cfg, metric)
        # Waits for a first token are under a second or two, so they get a second decimal place
        row[f"{metric} s"] = seconds if _wait(metric)[0] == "secs" else f"{seconds:.2f}"
    return row | {"$ / task": f"${sweep.value(cfg, 'usd'):.4f}", "tied with the fastest": tied}


def _color(name):
    return next(c for part, c in COLORS.items() if part in name.lower())


def _marks(settings):
    """A marker for each loop among the settings, in the order the tables list them"""
    loops = dict.fromkeys(cfg.loop_name for cfg in sorted(settings, key=lambda cfg: cfg.order[-1]))
    return dict(zip(loops, "osD^vP", strict=False))


def _entry(label, marker="o", color=SOFT_INK, lw=0, **look):
    """One line of a legend"""
    return Line2D([], [], marker=marker, color=color, lw=lw, label=label, **look)


def _tidy(ax, title):
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, loc="left", fontsize=11)


@plt.rc_context(BRAND)
def curve_chart(rows):
    """Seconds for a one-token reply against prompt length, one line for each model.
    rows: [{"model", "prompt tokens", "s"}]"""
    _, ax = plt.subplots(figsize=(7, 3.6))
    names = dict.fromkeys(r["model"] for r in rows)
    for name in names:
        points = [r for r in rows if r["model"] == name]
        xs = [p["prompt tokens"] / 1000 for p in points]
        ax.plot(xs, [p["s"] for p in points], marker="o", ms=5, color=_color(name))
    ax.set_xlabel("prompt tokens, thousands")
    ax.set_ylabel("seconds for a one-token reply")
    ax.set_xlim(0)
    ax.set_ylim(0)
    ax.grid(True)
    legend = [_entry(name, color=_color(name)) for name in names]
    ax.legend(handles=legend, frameon=False, fontsize=9, loc="upper left")
    _tidy(ax, "Latency vs. input prompt length")
    plt.show()


@plt.rc_context(BRAND)
def speed_chart(sweep, settings):
    """Every model call's seconds against its output tokens, with the line sweep.fit() draws through them, one
    color for each setting's model"""
    _, ax = plt.subplots(figsize=(7, 4))
    legend, tops = [], []
    for cfg in settings:
        rows = [r for rnd in sweep.rounds for r in sweep.rows[(cfg, rnd)]]
        tokens = np.concatenate([r["call_output_tokens"] for r in rows])
        secs = np.concatenate([r["call_secs"] for r in rows])
        color = _color(cfg.name)
        ax.scatter(tokens, secs, s=6, alpha=0.25, color=color, linewidths=0)
        a, b = sweep.fit(cfg)  # seconds per call, and per 100 output tokens
        end = np.percentile(tokens, 95)  # the line spans where most of the model's calls fall
        ax.plot([0, end], [a, a + b * end / 100], color=color, lw=2)
        tops.append((np.percentile(tokens, 99), np.percentile(secs, 99)))
        model = cfg.name.split(" · ")[0]
        legend.append(_entry(f"{model}, {round(100 / b)} tokens/s", color=color, lw=2, marker=""))
    # The axes stop at the 99th percentile, so a few long calls don't squash the rest
    ax.set_xlim(0, max(x for x, _ in tops))
    ax.set_ylim(0, max(y for _, y in tops))
    ax.set_xlabel("output tokens in the call")
    ax.set_ylabel("seconds for the call")
    ax.grid(True)
    ax.legend(handles=legend, frameon=False, fontsize=9, loc="upper left")
    _tidy(ax, "Call time vs. output tokens, at medium effort")
    plt.show()


@plt.rc_context(BRAND)
def frontier_chart(sweep, settings, bounds, pick, title):
    """Accuracy against seconds at bounds.metric, colored by model. The frontier runs over the settings that meet the bar,
    and only it and the pick get names"""
    metric = bounds.metric
    inside, marks = [cfg for cfg in settings if not bounds.outside(cfg)], _marks(settings)
    at = {cfg: (sweep.value(cfg, metric), sweep.value(cfg, "correct")) for cfg in settings}
    floor = min(0.9, bounds.bar - 0.03) - 0.01
    front = sweep.frontier(inside, metric)
    _, ax = plt.subplots(figsize=(10, 6))
    xs, ys = [at[cfg][0] for cfg in front], [at[cfg][1] for cfg in front]
    ax.step(
        [*xs, max(at[cfg][0] for cfg in inside)],
        [*ys, ys[-1]],
        where="post",
        color=GREY,
        lw=4,
        alpha=0.6,
        zorder=1,
    )
    for cfg in settings:
        (x, y), color = at[cfg], _color(cfg.name)
        edge = INK if cfg.speed == "fast" else color
        ax.plot(x, y, marks[cfg.loop_name], color=color, mec=edge, ms=8, zorder=3)
    ax.plot(*at[pick], "*", color=INK, mec=SURFACE, ms=22, zorder=5)
    named, heights = sorted({*front, pick}, key=lambda cfg: at[cfg][1]), []
    # Names sit in a column on the right, level with their markers, moved up where two would overlap
    for cfg in named:
        heights.append(max(at[cfg][1], heights[-1] + (1 - floor) / 28) if heights else at[cfg][1])
    for cfg, y in zip(named, np.array(heights) - max(0, heights[-1] - 1), strict=True):
        tie = {"arrowstyle": "-", "lw": 0.6, "color": _color(cfg.name), "alpha": 0.6}
        where = {"xytext": (1.01, y), "textcoords": ("axes fraction", "data"), "va": "center"}
        ax.annotate(cfg.name, at[cfg], fontsize=8.5, color=SOFT_INK, arrowprops=tie, **where)
    ax.axhline(bounds.bar, color=INK, ls="--", lw=1)
    label = f"quality bar {bounds.bar:.0%}"
    ax.annotate(label, (0.07, bounds.bar), xycoords=("axes fraction", "data"), va="top", fontsize=9)
    ax.set_xscale("log")
    ax.margins(x=0.06)
    ax.set_ylim(floor, 1.003)
    lo, hi = ax.get_xlim()
    ticks = [
        t for t in (0.3, 0.4, 0.5, 0.7, 1, 1.5, 2, 3, 4, 5, 7, 10, 15, 20, 30) if lo <= t <= hi
    ]
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.xaxis.set_minor_formatter(lambda *_: "")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    below = dict.fromkeys(
        cfg.with_loop("baseline loop").name for cfg in settings if at[cfg][1] < floor
    )
    note = f"\nMarkers under {floor:.0%} correct aren't drawn: {', '.join(below)}" if below else ""
    ax.set_xlabel(f"{in_words(metric)}, log scale{note}")
    ax.set_ylabel("tasks correct")
    legend = [_entry(loop, mark) for loop, mark in marks.items()]
    legend += [_entry("black outline: fast mode", mfc=GREY, mec=INK, color=SURFACE)]
    legend += [_entry(f"{name.title()} 5.5", color=c) for name, c in COLORS.items()]
    legend += [_entry("frontier of the settings that meet the bar", marker="", color=GREY, lw=4)]
    legend += [_entry("the fastest that meets the bar", "*", INK, mec=SURFACE, ms=13)]
    ax.legend(
        handles=legend,
        frameon=False,
        fontsize=8.5,
        ncols=5,
        loc="upper left",
        bbox_to_anchor=(0, -0.14 - 0.03 * bool(below)),
    )
    _tidy(ax, title)
    plt.show()
