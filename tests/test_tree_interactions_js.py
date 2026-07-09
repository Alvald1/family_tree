import subprocess
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TreeInteractionsZoomTest(unittest.TestCase):
    def run_node(self, script):
        result = subprocess.run(
            ["node", "-e", script],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail(result.stderr or result.stdout)
        return result.stdout

    def test_wheel_zoom_factor_is_smooth_and_bounded(self):
        script = textwrap.dedent(
            """
            global.window = { innerHeight: 900 };
            global.AppConfig = {
              viewer: {
                wheelZoomSensitivity: 0.0025,
                wheelZoomMaxStep: 0.04,
              },
            };
            global.Utils = {
              clamp(value, min, max) {
                return Math.min(Math.max(value, min), max);
              },
            };

            const TreeInteractions = require('./site/assets/js/tree-interactions.js');

            const smallTrackpadStep = TreeInteractions.getWheelZoomFactor({
              deltaY: 2,
              deltaMode: 0,
            });
            const largeZoomOutStep = TreeInteractions.getWheelZoomFactor({
              deltaY: 120,
              deltaMode: 0,
            });
            const largeZoomInStep = TreeInteractions.getWheelZoomFactor({
              deltaY: -120,
              deltaMode: 0,
            });
            const lineModeStep = TreeInteractions.normalizeWheelDelta({
              deltaY: 3,
              deltaMode: 1,
            });

            if (!(smallTrackpadStep < 1 && smallTrackpadStep > 0.99)) {
              throw new Error(`small trackpad step is not smooth: ${smallTrackpadStep}`);
            }
            if (largeZoomOutStep !== 0.96) {
              throw new Error(`large zoom out should be capped at 0.96: ${largeZoomOutStep}`);
            }
            if (largeZoomInStep !== 1.04) {
              throw new Error(`large zoom in should be capped at 1.04: ${largeZoomInStep}`);
            }
            if (lineModeStep !== 48) {
              throw new Error(`line-mode delta should normalize to pixels: ${lineModeStep}`);
            }
            """
        )

        self.run_node(script)


if __name__ == "__main__":
    unittest.main()
