/**
 * Drone Safari — PixiJS v8 renderer + cockpit wiring.
 * Renders the game grid from game-core.js, handles keyboard/button input,
 * and keeps the HUD, album, log, and win/lose overlay in sync.
 */
(function () {
  "use strict";

  var S = window.DroneSafari;
  var game = new S.DroneSafariGame("medium");

  // ---------------------------------------------------------------- Pixi app
  var app = new PIXI.Application();
  var board,
    cellSize,
    sprites = {};

  var TILE_FILES = {
    tree: "images/tree.png",
    zebra: "images/zebra.png",
    elephant: "images/elephant.png",
    oryx: "images/oryx.png",
    drone: "images/drone.png",
    crashed: "images/crashed_drone.png",
    scared: "images/scared_animal.png",
    shining: "images/shining.png",
  };

  // Ground colors adapt to theme (redrawn on theme change)
  function groundColors() {
    var dark = document.documentElement.getAttribute("data-theme") === "dark";
    return {
      panel: dark ? 0x0d1526 : 0xffffff,
      panelBorder: dark ? 0x2e3f5e : 0x0f172a,
      empty: dark ? 0x151f38 : 0xffffff,
      grid: dark ? 0x3d4f6e : 0xdfe6f0,
      tree: dark ? 0x1b4332 : 0xf0fdf4,
      photo: dark ? 0x1e293b : 0xfffbeb,
      trail: dark ? 0x7dd3fc : 0x64748b,
      banner: dark ? 0x111827 : 0xffffff,
      bannerBorder: dark ? 0x64748b : 0x0f172a,
      bannerText: dark ? 0xf1f5f9 : 0x0f172a,
      bannerMuted: dark ? 0xcbd5e1 : 0x475569,
      bannerFail: dark ? 0xfb7185 : 0xdc2626,
      bannerWin: dark ? 0x34d399 : 0x059669,
    };
  }

  async function init() {
    await app.init({
      resizeTo: document.getElementById("pixi-stage"),
      backgroundAlpha: 0,
      antialias: true,
    });
    document.getElementById("pixi-stage").appendChild(app.canvas);

    // Load sprite textures
    var textureNames = Object.keys(TILE_FILES);
    var textureMap = await PIXI.Assets.load(
      Object.values(TILE_FILES).map(function (p) {
        return { src: p };
      }),
    );
    textureNames.forEach(function (name) {
      sprites[name] = textureMap[TILE_FILES[name]];
    });

    // Root container for the whole board
    board = new PIXI.Container();
    app.stage.addChild(board);
    app.stage.eventMode = "static";

    window.addEventListener("resize", layout);
    layout();
    render();

    wireInput();
    wireGuide();
    log(
      "🛰️ Game started — difficulty: " +
        game.difficulty +
        " (" +
        game.message +
        ")",
    );
  }

  /** Compute cell size + board position to fit the stage with margin. */
  function layout() {
    var stage = document.getElementById("pixi-stage");
    var w = stage.clientWidth;
    var h = stage.clientHeight;
    var margin = Math.min(48, w * 0.06);
    var boardPx = Math.max(240, Math.min(w - margin * 2, h - margin * 2 - 8));
    cellSize = boardPx / S.GRID_SIZE;
    board.x = (w - boardPx) / 2;
    board.y = (h - boardPx) / 2;
    board.scale.set(1);
  }

  // ---------------------------------------------------------------- rendering
  function render() {
    board.removeChildren();
    var colors = groundColors();

    // Board panel (rounded card behind the grid)
    var boardPx = cellSize * S.GRID_SIZE;
    var panel = new PIXI.Graphics();
    panel
      .roundRect(
        -boardPx * 0.035,
        -boardPx * 0.035,
        boardPx * 1.07,
        boardPx * 1.07,
        18,
      )
      .fill({ color: colors.panel })
      .stroke({ width: 2, color: colors.panelBorder, alpha: 0.85 });
    board.addChild(panel);

    // Grid cells
    for (var r = 0; r < S.GRID_SIZE; r++) {
      for (var c = 0; c < S.GRID_SIZE; c++) {
        var cell = new PIXI.Graphics();
        var x = c * cellSize;
        var y = (S.GRID_SIZE - 1 - r) * cellSize; // row 0 at the bottom

        var v = game.grid[r][c];
        var fill = v === S.TREE ? colors.tree : colors.empty;
        cell.rect(x, y, cellSize, cellSize).fill(fill);
        cell
          .rect(x, y, cellSize, cellSize)
          .stroke({ width: 1, color: colors.grid });
        board.addChild(cell);
      }
    }

    // Grid lines on top of the cells for crisp visibility in both themes
    var lines = new PIXI.Graphics();
    for (var g = 0; g <= S.GRID_SIZE; g++) {
      lines
        .moveTo(g * cellSize, 0)
        .lineTo(g * cellSize, boardPx)
        .moveTo(0, g * cellSize)
        .lineTo(boardPx, g * cellSize);
    }
    lines.stroke({ width: 1.5, color: colors.grid, alpha: 0.9 });
    board.addChild(lines);

    // Movement trail (visual only — lines between consecutive moves)
    // We re-derive the trail from the last few positions via a trail array kept by render loop
    drawTrail(colors.trail);

    // Photo markers
    Object.keys(game.photographed_locations).forEach(function (key) {
      var parts = key.split(",").map(Number);
      var pr = parts[0];
      var pc = parts[1];
      if (!game._is_valid_position(pr, pc)) return;
      var mark = new PIXI.Graphics();
      mark
        .circle(
          (pc + 0.5) * cellSize,
          (S.GRID_SIZE - 1 - pr + 0.5) * cellSize,
          cellSize * 0.3,
        )
        .fill({ color: 0xfbbf24, alpha: 0.35 })
        .stroke({ width: 2, color: 0xf59e0b });
      board.addChild(mark);
    });

    // Scared-animal markers
    game.scared_animals.forEach(function (pos) {
      var sr = pos[0];
      var sc = pos[1];
      var s = new PIXI.Sprite(sprites.scared);
      s.width = cellSize * 0.9;
      s.height = cellSize * 0.9;
      s.anchor.set(0.5);
      s.x = (sc + 0.5) * cellSize;
      s.y = (S.GRID_SIZE - 1 - sr + 0.5) * cellSize;
      s.alpha = 0.75;
      board.addChild(s);
    });

    // Entities: trees + animals
    for (var r2 = 0; r2 < S.GRID_SIZE; r2++) {
      for (var c2 = 0; c2 < S.GRID_SIZE; c2++) {
        var val = game.grid[r2][c2];
        if (val === S.EMPTY) continue;
        var texName =
          val === S.TREE
            ? "tree"
            : val === S.ZEBRA
              ? "zebra"
              : val === S.ELEPHANT
                ? "elephant"
                : "oryx";
        var spr = new PIXI.Sprite(sprites[texName]);
        spr.width = cellSize * 0.92;
        spr.height = cellSize * 0.92;
        spr.anchor.set(0.5);
        spr.x = (c2 + 0.5) * cellSize;
        spr.y = (S.GRID_SIZE - 1 - r2 + 0.5) * cellSize;
        board.addChild(spr);
      }
    }

    // Drone (rotated to its facing direction; North = up on screen)
    var drone = new PIXI.Sprite(
      game.game_over ? sprites.crashed : sprites.drone,
    );
    drone.width = cellSize * 0.95;
    drone.height = cellSize * 0.95;
    drone.anchor.set(0.5);
    drone.x = (game.drone_pos[1] + 0.5) * cellSize;
    drone.y = (S.GRID_SIZE - 1 - game.drone_pos[0] + 0.5) * cellSize;
    drone.rotation = {
      North: 0,
      East: Math.PI / 2,
      South: Math.PI,
      West: -Math.PI / 2,
    }[game.drone_facing];
    board.addChild(drone);

    updateHud();
    updateBanner();
  }

  var _lastTrailPos = null;
  function drawTrail(color) {
    // Cheap trail: connect previous positions stored on each render via module var
    if (_lastTrailPos && !game.game_over) {
      var g = new PIXI.Graphics();
      g.moveTo(
        (_lastTrailPos[1] + 0.5) * cellSize,
        (S.GRID_SIZE - 1 - _lastTrailPos[0] + 0.5) * cellSize,
      );
      g.lineTo(
        (game.drone_pos[1] + 0.5) * cellSize,
        (S.GRID_SIZE - 1 - game.drone_pos[0] + 0.5) * cellSize,
      );
      g.stroke({
        width: Math.max(2, cellSize * 0.06),
        color: color,
        alpha: 0.6,
        cap: "round",
      });
      board.addChild(g);
    }
    _lastTrailPos = game.drone_pos.slice();
  }

  // ---------------------------------------------------------------- HUD
  function updateHud() {
    var st = game.get_status();
    document.getElementById("hud-pos").textContent = st.position.join(", ");
    document.getElementById("hud-facing").textContent = st.facing;
    document.getElementById("hud-pics").textContent = st.pictures_remaining;
    document.getElementById("hud-moves").textContent =
      st.total_moves + " / " + st.total_turns;
    ["zebra", "elephant", "oryx"].forEach(function (k) {
      document
        .getElementById("album-" + k)
        .classList.toggle("captured", st.animals_photographed[k]);
    });
  }

  // ---------------------------------------------------------------- logging
  function log(msg) {
    var el = document.getElementById("log");
    var div = document.createElement("div");
    div.textContent = "› " + msg;
    if (/wasted|crash|crashed|scared|blocking|No pictures/i.test(msg))
      div.className = "log-bad";
    else if (/Successfully|won|Congratulations/i.test(msg))
      div.className = "log-good";
    else if (/Sensors/i.test(msg)) div.className = "log-warn";
    el.appendChild(div);
    while (el.children.length > 60) el.removeChild(el.firstChild);
    el.scrollTop = el.scrollHeight;
  }

  // ---------------------------------------------------------------- actions
  function doAction(action) {
    if (game.game_over) return;
    var msg;
    if (action === "move-forward") msg = game.move("forward");
    else if (action === "move-backward") msg = game.move("backward");
    else if (action === "turn-left") msg = game.turn("left");
    else if (action === "turn-right") msg = game.turn("right");
    else if (action === "picture") msg = game.take_picture();
    render();
    log(msg.split("\n")[0]);
  }

  function doSensors() {
    if (game.game_over) return;
    log(game._get_sensor_summary());
  }

  function restart() {
    game.reset_game();
    _lastTrailPos = null;
    render();
    log("🔄 Restarted — difficulty: " + game.difficulty);
  }

  /** Crisp DOM notification card overlaid on the canvas (board stays visible). */
  function updateBanner() {
    var banner = document.getElementById("game-banner");
    if (!game.game_over) {
      banner.classList.add("hidden");
      return;
    }

    var emoji = game.game_won ? "🏆" : "💥";
    var title = game.game_won ? "Mission Accomplished!" : "Mission Failed";
    var reason = game.failure_reason || "mission_incomplete";
    var sub =
      {
        boundary_crash: "The drone flew out of the park boundaries.",
        tree_crash: "The drone crashed into a tree.",
        animal_crash: "The drone crashed into an animal.",
        scared_animal: "Too close! An animal got scared and ran away.",
        out_of_pictures: "Out of pictures — the safari mission is incomplete.",
      }[reason] || "The mission ended.";

    document.getElementById("game-banner-emoji").textContent = emoji;
    document.getElementById("game-banner-title").textContent = title;
    document.getElementById("game-banner-sub").textContent =
      sub + "  ·  press R to restart";
    banner.classList.toggle("fail", !game.game_won);
    banner.classList.toggle("win", game.game_won);

    // Position over the board (stage = canvas = board coordinate space)
    var boardPx = cellSize * S.GRID_SIZE;
    var bannerW = Math.min(560, boardPx * 0.92);
    var stage = document.getElementById("pixi-stage");
    var left = board.x + (boardPx - bannerW) / 2;
    var top = board.y + cellSize * 0.6;
    banner.style.left = left + "px";
    banner.style.top = top + "px";
    banner.style.width = bannerW + "px";
    banner.classList.remove("hidden");
  }

  // ---------------------------------------------------------------- guide modal
  var guideOpen = false;
  function wireGuide() {
    function open() {
      guideOpen = true;
      document.getElementById("guide").classList.remove("hidden");
    }
    function close() {
      guideOpen = false;
      document.getElementById("guide").classList.add("hidden");
    }
    document.getElementById("btn-guide").addEventListener("click", open);
    document.querySelectorAll("[data-close-guide]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && guideOpen) close();
    });
  }

  // ---------------------------------------------------------------- input
  function wireInput() {
    document.addEventListener("keydown", function (e) {
      if (e.repeat) return;
      if (guideOpen) return; // guide modal owns the keyboard while open
      var key = e.key;
      if (key === "ArrowUp" || key === "w" || key === "W")
        doAction("move-forward");
      else if (key === "ArrowDown" || key === "s" || key === "S")
        doAction("move-backward");
      else if (key === "ArrowLeft" || key === "a" || key === "A")
        doAction("turn-left");
      else if (key === "ArrowRight" || key === "d" || key === "D")
        doAction("turn-right");
      else if (key === " " || key === "Enter") doAction("picture");
      else if (key === "r" || key === "R") restart();
      else if (key === "q" || key === "Q") {
        if (confirm("Quit the safari game?")) window.close();
      } else return;
      e.preventDefault();
    });

    document.querySelectorAll("[data-action]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        doAction(btn.getAttribute("data-action"));
      });
    });
    document.getElementById("btn-sensors").addEventListener("click", doSensors);
    document.getElementById("btn-restart").addEventListener("click", restart);

    document
      .getElementById("difficulty")
      .addEventListener("change", function (e) {
        game = new S.DroneSafariGame(e.target.value);
        _lastTrailPos = null;
        render();
        log("🗺️ Difficulty set to " + game.difficulty);
      });

    document.getElementById("btn-theme").addEventListener("click", function () {
      var current =
        document.documentElement.getAttribute("data-theme") || "dark";
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
      render();
    });

    if (window.matchMedia) {
      window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", function (ev) {
          if (!localStorage.getItem("theme")) {
            document.documentElement.setAttribute(
              "data-theme",
              ev.matches ? "dark" : "light",
            );
            render();
          }
        });
    }
  }

  init();
})();
