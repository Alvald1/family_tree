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

    def test_viewer_config_uses_faster_wheel_zoom_step(self):
        script = textwrap.dedent(
            """
            const AppConfig = require('./site/assets/js/config.js');

            if (AppConfig.viewer.wheelZoomMaxStep !== 0.04) {
              throw new Error(`wheel zoom max step should be 0.04: ${AppConfig.viewer.wheelZoomMaxStep}`);
            }
            """
        )

        self.run_node(script)

    def test_tree_viewer_fetches_svg_with_asset_version(self):
        script = textwrap.dedent(
            """
            (async () => {
            global.window = {};
            global.document = {
              getElementById() {
                return {
                  innerHTML: '',
                  querySelector() {
                    return null;
                  },
                };
              },
            };
            global.AppConfig = {
              files: {
                familyTreeSvg: 'family_tree_vector.svg',
              },
              assets: {
                version: 'tree-node-id-20260709-1',
              },
              viewer: {
                defaultZoom: 1,
              },
              messages: {
                loading: 'loading',
                loadError: 'error',
                fileNotFound: 'missing',
                networkError: 'network',
              },
              icons: {
                error: 'error',
              },
            };

            const fetchedUrls = [];
            global.Utils = {
              fetchStatic(url) {
                fetchedUrls.push(url);
                return Promise.reject(new Error('stop after fetch url capture'));
              },
            };

            const TreeViewer = require('./site/assets/js/tree-viewer.js');
            const viewer = Object.create(TreeViewer.prototype);
            viewer.container = document.getElementById('svgContainer');
            viewer.showLoading = () => {};
            viewer.showError = () => {};

            await viewer.loadSVG();

            if (fetchedUrls[0] !== 'family_tree_vector.svg?v=tree-node-id-20260709-1') {
              throw new Error(`unexpected SVG URL: ${fetchedUrls[0]}`);
            }
            })().catch((error) => {
              setTimeout(() => {
                throw error;
              }, 0);
            });
            """
        )

        self.run_node(script)

    def test_person_nodes_open_context_menu_instead_of_double_click(self):
        script = textwrap.dedent(
            """
            global.window = {};
            global.document = {
              createElementNS() {
                return {
                  textContent: '',
                  setAttribute() {},
                };
              },
            };
            global.AppConfig = {
              messages: {
                personClickHint: 'Правый клик для открытия меню персоны',
              },
            };

            const TreeViewer = require('./site/assets/js/tree-viewer.js');
            const viewer = Object.create(TreeViewer.prototype);
            const listeners = {};
            const node = {
              style: {},
              getAttribute(name) {
                return name === 'id' ? 'node7' : null;
              },
              querySelector(selector) {
                if (selector === 'title') {
                  return { textContent: '7' };
                }
                return null;
              },
              querySelectorAll() {
                return [];
              },
              appendChild() {},
            };

            viewer.svg = {
              addEventListener(type, handler) {
                listeners[type] = handler;
              },
              querySelectorAll(selector) {
                if (selector === 'g.node:not([id*="marriage"])') {
                  return [node];
                }
                return [];
              },
            };

            viewer.addPersonClickHandlers();

            if (listeners.dblclick) {
              throw new Error('double click should not open person profile');
            }
            if (!listeners.contextmenu) {
              throw new Error('right click should open person context menu');
            }
            """
        )

        self.run_node(script)

    def test_person_id_comes_from_graphviz_title_not_svg_group_id(self):
        script = textwrap.dedent(
            """
            const TreeViewer = require('./site/assets/js/tree-viewer.js');

            const node = {
              getAttribute(name) {
                return name === 'id' ? 'node9' : null;
              },
              querySelector(selector) {
                if (selector === 'title') {
                  return { textContent: '7' };
                }
                return null;
              },
            };

            const personId = TreeViewer.getPersonIdFromNode(node);

            if (personId !== 'node7') {
              throw new Error(`expected person id node7 from title, got ${personId}`);
            }
            """
        )

        self.run_node(script)

    def test_non_numeric_graphviz_title_is_not_person_node(self):
        script = textwrap.dedent(
            """
            const TreeViewer = require('./site/assets/js/tree-viewer.js');

            const marriageNode = {
              getAttribute(name) {
                return name === 'id' ? 'node151' : null;
              },
              querySelector(selector) {
                if (selector === 'title') {
                  return { textContent: 'marriage_3' };
                }
                return null;
              },
            };

            const personId = TreeViewer.getPersonIdFromNode(marriageNode);

            if (personId !== null) {
              throw new Error(`marriage node should not be treated as a person: ${personId}`);
            }
            """
        )

        self.run_node(script)

    def test_context_menu_uses_person_id_from_graphviz_title(self):
        script = textwrap.dedent(
            """
            const TreeViewer = require('./site/assets/js/tree-viewer.js');
            const viewer = Object.create(TreeViewer.prototype);
            const node = {
              getAttribute(name) {
                return name === 'id' ? 'node9' : null;
              },
              querySelector(selector) {
                if (selector === 'title') {
                  return { textContent: '7' };
                }
                return null;
              },
            };

            viewer.showPersonContextMenu = (personId, clientX, clientY) => {
              viewer.openedMenu = { personId, clientX, clientY };
            };

            viewer.handleNodeContextMenu({
              target: {
                closest(selector) {
                  return selector === 'g.node' ? node : null;
                },
              },
              clientX: 100,
              clientY: 200,
              preventDefault() {
                viewer.prevented = true;
              },
              stopPropagation() {
                viewer.stopped = true;
              },
            });

            if (!viewer.prevented || !viewer.stopped) {
              throw new Error('person context menu event should be captured');
            }
            if (!viewer.openedMenu || viewer.openedMenu.personId !== 'node7') {
              throw new Error(`expected menu for node7, got ${JSON.stringify(viewer.openedMenu)}`);
            }
            """
        )

        self.run_node(script)

    def test_person_context_menu_open_profile_button_navigates(self):
        script = textwrap.dedent(
            """
            global.AppConfig = {
              messages: {
                openPersonProfile: 'Открыть профиль',
              },
              autoSave: { enabled: false },
            };
            global.Utils = {
              createElement(tagName, attributes = {}, textContent = '') {
                const element = {
                  tagName,
                  attributes,
                  textContent,
                  style: {},
                  children: [],
                  listeners: {},
                  offsetWidth: 160,
                  offsetHeight: 44,
                  appendChild(child) {
                    this.children.push(child);
                  },
                  addEventListener(type, handler) {
                    this.listeners[type] = handler;
                  },
                  remove() {
                    this.removed = true;
                  },
                  contains(target) {
                    return target === this || this.children.includes(target);
                  },
                };
                return element;
              },
              clamp(value, min, max) {
                return Math.min(Math.max(value, min), max);
              },
            };

            const TreeViewer = require('./site/assets/js/tree-viewer.js');
            const viewer = Object.create(TreeViewer.prototype);
            const appended = [];

            viewer.container = {
              appendChild(element) {
                appended.push(element);
              },
              getBoundingClientRect() {
                return { left: 10, top: 20, width: 500, height: 300 };
              },
            };
            viewer.openPersonPage = (personId) => {
              viewer.openedPersonId = personId;
            };

            viewer.showPersonContextMenu('node7', 110, 120);

            const menu = appended[0];
            const button = menu.children[0];
            if (button.textContent !== 'Открыть профиль') {
              throw new Error(`unexpected menu item text: ${button.textContent}`);
            }

            button.listeners.click({
              preventDefault() {},
              stopPropagation() {},
            });

            if (viewer.openedPersonId !== 'node7') {
              throw new Error(`profile should open for node7: ${viewer.openedPersonId}`);
            }
            if (!menu.removed) {
              throw new Error('menu should close before navigation');
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
