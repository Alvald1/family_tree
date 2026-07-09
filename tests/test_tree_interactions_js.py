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
                wheelZoomSensitivity: 0.0012,
                wheelZoomMaxStep: 0.02,
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
            if (largeZoomOutStep !== 0.98) {
              throw new Error(`large zoom out should be capped at 0.98: ${largeZoomOutStep}`);
            }
            if (largeZoomInStep !== 1.02) {
              throw new Error(`large zoom in should be capped at 1.02: ${largeZoomInStep}`);
            }
            if (lineModeStep !== 48) {
              throw new Error(`line-mode delta should normalize to pixels: ${lineModeStep}`);
            }
            """
        )

        self.run_node(script)

    def test_tree_viewer_uses_top_left_transform_origin_for_cursor_zoom(self):
        script = textwrap.dedent(
            """
            global.window = {};
            global.document = {
              createElementNS() {
                return { textContent: '' };
              },
            };
            global.AppConfig = {
              viewer: {
                defaultZoom: 1,
                minZoom: 0.1,
                maxZoom: 5,
              },
              autoSave: { enabled: false },
              messages: {},
            };
            global.Utils = {
              clamp(value, min, max) {
                return Math.min(Math.max(value, min), max);
              },
            };

            const TreeViewer = require('./site/assets/js/tree-viewer.js');
            const viewer = Object.create(TreeViewer.prototype);
            viewer.svg = {
              style: {},
              setAttribute() {},
              querySelectorAll() { return []; },
              addEventListener() {},
            };
            viewer.addPersonClickHandlers = () => {};
            viewer.updateTransform = () => {};

            viewer.setupSVG();

            if (viewer.svg.style.transformOrigin !== '0 0') {
              throw new Error(`transform origin should be top-left: ${viewer.svg.style.transformOrigin}`);
            }
            """
        )

        self.run_node(script)


if __name__ == "__main__":
    unittest.main()
