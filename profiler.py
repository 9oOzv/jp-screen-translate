import cProfile
import pstats
from pathlib import Path


class Profiler():

    def __init__(
        self,
        file: str | Path | None = None,
    ):
        self.file = file

    def profile(self, f: callable):
        self.profile = cProfile.Profile()
        with self.profile:
            f()
        self.profile_stats = pstats.Stats(self.profile)
        if self.file:
            self._save_profile()
        else:
            self._print_profile()

    def _print_profile(self):
        print(
            '\n'
            .join(self._profile_lines())
        )

    def _save_profile(self):
        file = self.file
        with open(file, 'w') as f:
            f.write(
                '\n'
                .join(self._profile_lines())
            )

    def _profile_lines(self):
        stat_items = self.profile_stats.stats.items()
        stats = []
        for func, (cc, nc, tt, ct, callers) in stat_items:
            stats.append({
                'path': func[0],
                'line': func[1],
                'func': func[2],
                'stdname': cc,
                'calls': nc,
                'time': tt,
                'cumulative': ct,
            })
        stats = sorted(
            stats,
            key=lambda x: x['cumulative'],
            reverse=True
        )

        def statline(s):
            filename = Path(s['path']).name
            cols = [
                f'{filename:20.20}',
                f'{str(s["line"]):4.4}',
                f'{s["func"]:20.20}',
                f'{s["cumulative"]:.3f} seconds',
            ]
            return '  '.join(cols)

        return [
            statline(s)
            for s in stats
        ]
