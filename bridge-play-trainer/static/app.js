"use strict";

const SEATS = ["N", "E", "S", "W"];
const SUIT_SYMBOL = { S: "♠", H: "♥", D: "♦", C: "♣" };
const SUIT_NAME = { S: "Spades", H: "Hearts", D: "Diamonds", C: "Clubs" };
const RED_SUITS = new Set(["H", "D"]);

let sessionId = null;
let lastState = null;
let viewingLastTrick = false;
let trickFreeze = null;             // { plays: [...] } while we pause to show the completed trick
let auctionAnimating = false;
let auctionVisibleCount = null;     // null = show full auction; otherwise number of bids to reveal
let auctionAnimationToken = 0;      // bumped to cancel in-flight animations when a new deal starts
let awaitingPlay = false;           // auction is fully revealed; waiting for the user to click Play

let reviewingAuction = false;       // user is holding the Review button

function bidsInCenter() { return auctionAnimating || awaitingPlay || reviewingAuction; }
const TRICK_HOLD_MS = 3000;
const AUCTION_CALL_MS = 1300;       // substantive bids
const AUCTION_PASS_MS = 700;        // passes/doubles go faster, like at a real table
const playedVisible = { N: false, E: false, S: false, W: false };

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function togglePlayed(seatLetter) {
  playedVisible[seatLetter] = !playedVisible[seatLetter];
  if (lastState) render(lastState);
}

function toggleLastTrick() {
  if (!lastState || !lastState.trick_history || lastState.trick_history.length === 0) return;
  viewingLastTrick = !viewingLastTrick;
  render(lastState);
}

// ---------- helpers ----------

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    e.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return e;
}

function suitClass(suit) { return RED_SUITS.has(suit) ? "suit-red" : "suit-black"; }

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

// ---------- rendering ----------

// Render a hand as 4 suit rows of clickable card buttons. Cards are clickable
// only when it's this seat's turn and the user controls this seat — otherwise
// they appear dimmed. Illegal cards (must-follow-suit) are also dimmed.
function renderHand(hand, opts) {
  const { isCurrentSeat, userControlsSeat, legalSet } = opts;
  const rows = [];
  for (const suit of ["S", "H", "D", "C"]) {
    const ranks = (hand && hand[suit]) ? hand[suit] : [];
    const row = el("div", { class: `hand-suit ${suitClass(suit)}` });
    row.appendChild(el("span", { class: "suit-symbol" }, SUIT_SYMBOL[suit]));
    if (ranks.length === 0) {
      row.appendChild(el("span", { class: "muted" }, "—"));
    } else {
      for (const rank of ranks) {
        const isLegal = isCurrentSeat && userControlsSeat && legalSet.has(`${suit}${rank}`);
        const cls = `card-btn ${suitClass(suit)} ${isLegal ? "legal" : "illegal"}`;
        const btn = el("span", {
          class: cls,
          ...(isLegal ? { onclick: () => playCard(suit, rank) } : {}),
        }, rank);
        row.appendChild(btn);
      }
    }
    rows.push(row);
  }
  return rows;
}

function renderSeatInto(slot, seatLetter, state) {
  slot.innerHTML = "";
  slot.classList.remove("face-down", "active");
  if (seatLetter === null) {
    return;
  }

  let title = seatLetter;
  if (seatLetter === state.declarer) title += " (declarer)";
  if (seatLetter === state.dummy) title += " (dummy)";
  if (state.to_play === seatLetter && !state.complete) {
    slot.classList.add("active");
  }
  slot.appendChild(el("div", { class: "seat-name" }, title));

  // At end of deal: reveal all four hands from the result payload.
  const hand = state.complete && state.result && state.result.all_hands
    ? state.result.all_hands[seatLetter]
    : state.hands[seatLetter];
  if (hand === null) {
    slot.classList.add("face-down");
    slot.appendChild(el("div", { class: "muted" }, "Hidden"));
    const played = (bidsInCenter() ? [] : (state.cards_played_by_seat[seatLetter] || []));
    if (played.length) {
      const strip = el("div", { class: "played-strip" });
      const visible = !!playedVisible[seatLetter];
      const toggle = el("button", {
        class: "played-toggle",
        onclick: () => togglePlayed(seatLetter),
      }, visible ? `Hide played (${played.length})` : `Show played (${played.length})`);
      strip.appendChild(toggle);
      if (visible) {
        const cards = el("div", { class: "played-cards" });
        for (const c of played) {
          const symbol = c[0];
          const klass = (symbol === "♥" || symbol === "♦") ? "suit-red" : "";
          cards.appendChild(el("span", { class: `played-card ${klass}` }, c));
        }
        strip.appendChild(cards);
      }
      slot.appendChild(strip);
    }
    return;
  }

  const isCurrentSeat = state.to_play === seatLetter && !state.complete && !trickFreeze && !bidsInCenter();
  const userControlsSeat = state.user_to_play && isCurrentSeat;
  const legalSet = new Set(state.legal_moves.map(m => `${m.suit}${m.rank}`));
  for (const row of renderHand(hand, { isCurrentSeat, userControlsSeat, legalSet })) {
    slot.appendChild(row);
  }
  if (userControlsSeat) {
    slot.appendChild(el("div", { class: "seat-prompt" }, "Your move — click a card."));
  }
}

function fillAuctionGrid(grid, state, opts = {}) {
  const { largeStyle = false } = opts;
  grid.innerHTML = "";
  for (const s of ["W", "N", "E", "S"]) {
    grid.appendChild(el("div", { class: "auction-cell header" }, s));
  }
  const order = ["W", "N", "E", "S"];
  const dealerIdx = order.indexOf(state.dealer);
  for (let i = 0; i < dealerIdx; i++) {
    grid.appendChild(el("div", { class: "auction-cell empty" }, "—"));
  }
  const visibleCalls = (auctionVisibleCount === null)
    ? state.auction
    : state.auction.slice(0, auctionVisibleCount);
  visibleCalls.forEach((call, idx) => {
    const cell = el("div", { class: "auction-cell" });
    appendCallWithColoredSuit(cell, call.call);
    if (call.annotation) cell.title = call.annotation;
    if (auctionAnimating && idx === visibleCalls.length - 1) {
      cell.classList.add("auction-cell-new");
    }
    grid.appendChild(cell);
  });
}

function renderAuction(state) {
  // The right-side auction panel is gone; the bidding box in the centre shows
  // the auction during animation and is dismissed when the user clicks Play.
  // Nothing to render here outside of that.
}

function userSideLabel(state) {
  const userSeat = userPrimarySeat(state);
  return (userSeat === "N" || userSeat === "S") ? "NS" : "EW";
}

function renderTricksStrip(state) {
  const strip = document.getElementById("tricks-strip");
  strip.innerHTML = "";
  if (bidsInCenter()) return;
  const history = state.trick_history || [];
  if (history.length === 0) return;
  const ourSide = userSideLabel(state);
  for (const t of history) {
    const winnerSide = (t.winner === "N" || t.winner === "S") ? "NS" : "EW";
    const klass = winnerSide === ourSide ? "ours" : "theirs";
    strip.appendChild(el("div", {
      class: `trick-back ${klass}`,
      title: `Trick ${t.n} — won by ${t.winner}`,
    }));
  }
}

function appendCallWithColoredSuit(cell, callText) {
  // Server sends bids like "1♠", "3NT", "Pass", "X". Color the suit symbol.
  const symMap = { "♠": "suit-black", "♥": "suit-red", "♦": "suit-red", "♣": "suit-black" };
  const ntMatch = callText.match(/^(\d+)NT$/);
  if (ntMatch) {
    cell.appendChild(document.createTextNode(ntMatch[1] + "NT"));
    return;
  }
  const m = callText.match(/^(\d+)([♠♥♦♣])$/);
  if (m) {
    cell.appendChild(document.createTextNode(m[1]));
    cell.appendChild(el("span", { class: symMap[m[2]] }, m[2]));
    return;
  }
  cell.appendChild(document.createTextNode(callText));
}

function renderContractDisplay(state) {
  const box = document.getElementById("contract-display");
  box.innerHTML = "";
  const sym = state.strain_symbol;  // ♠/♥/♦/♣/NT
  const symKlass =
    sym === "♥" || sym === "♦" ? "suit-red" :
    sym === "♠" || sym === "♣" ? "suit-black" : "";
  const main = el("div", { class: "contract-line-main" });
  main.appendChild(el("span", {}, String(state.level)));
  main.appendChild(el("span", { class: symKlass }, sym));
  box.appendChild(main);
  box.appendChild(el("div", { class: "contract-line-sub" }, `Dealer: ${state.dealer}`));
}

// Map of compass seats to UI slot positions. The user's seat goes at the
// bottom, partner at top, LHO at left, RHO at right. Play visually goes
// clockwise: bottom → left → top → right.
const SEAT_ORDER = ["N", "E", "S", "W"];
function seatOffset(seat) { return SEAT_ORDER.indexOf(seat); }
function partnerOf(seat) { return SEAT_ORDER[(seatOffset(seat) + 2) % 4]; }
function lhoOf(seat) { return SEAT_ORDER[(seatOffset(seat) + 1) % 4]; }
function rhoOf(seat) { return SEAT_ORDER[(seatOffset(seat) + 3) % 4]; }

function userPrimarySeat(state) {
  if (state.role === "leader") return lhoOf(state.declarer);
  if (state.role === "defender") return rhoOf(state.declarer);
  return state.declarer;
}

function slotLayout(state) {
  const bottom = userPrimarySeat(state);
  return {
    bottom,
    top: partnerOf(bottom),
    left: lhoOf(bottom),
    right: rhoOf(bottom),
  };
}

function renderTable(state) {
  const layout = slotLayout(state);
  renderSeatInto(document.getElementById("slot-top"), layout.top, state);
  renderSeatInto(document.getElementById("slot-bottom"), layout.bottom, state);
  renderSeatInto(document.getElementById("slot-left"), layout.left, state);
  renderSeatInto(document.getElementById("slot-right"), layout.right, state);

  const center = document.getElementById("center");
  center.innerHTML = "";
  center.classList.remove("reviewing");
  center.onclick = toggleLastTrick;

  const seatToPosition = {
    [layout.top]: "top",
    [layout.right]: "right",
    [layout.bottom]: "bottom",
    [layout.left]: "left",
  };

  const hasHistory = state.trick_history && state.trick_history.length > 0;
  const showReview = viewingLastTrick && hasHistory && !trickFreeze;

  // Review (press-and-hold auction) takes priority over trick freeze and
  // last-trick peek so the user can always recall the bidding during play.
  if (bidsInCenter()) {
    const wrap = el("div", { class: "center-auction-box" });
    const grid = el("div", { class: "center-auction-grid" });
    fillAuctionGrid(grid, state, { largeStyle: true });
    wrap.appendChild(grid);
    if (awaitingPlay) {
      const playBtn = el("button", {
        class: "primary center-play-btn",
        onclick: startPlay,
      }, "Play");
      wrap.appendChild(playBtn);
    }
    center.appendChild(wrap);
    return;
  }

  if (trickFreeze) {
    center.classList.add("reviewing");
    center.appendChild(el("div", { class: "center-trick-label" },
      `Trick #${trickFreeze.n} — ${trickFreeze.winner} won`));
    for (const p of trickFreeze.plays) {
      const symbol = p.card[0];
      const suitKlass = (symbol === "♥" || symbol === "♦") ? "suit-red" : "suit-black";
      const pos = seatToPosition[p.seat];
      const posKlass = pos ? `center-trick-${pos}` : "";
      center.appendChild(el("div", { class: `trick-card ${suitKlass} ${posKlass}` }, p.card));
    }
    return;
  }

  if (showReview) {
    const last = state.trick_history[state.trick_history.length - 1];
    center.classList.add("reviewing");
    center.appendChild(el("div", { class: "center-trick-label" },
      `Last trick (#${last.n}) — ${last.winner} won · click to return`));
    for (const p of last.plays) {
      const symbol = p.card[0];
      const suitKlass = (symbol === "♥" || symbol === "♦") ? "suit-red" : "suit-black";
      const pos = seatToPosition[p.seat];
      const posKlass = pos ? `center-trick-${pos}` : "";
      center.appendChild(el("div", { class: `trick-card ${suitKlass} ${posKlass}` }, p.card));
    }
    return;
  }

  if (state.complete) {
    const r = state.result;
    const declSym = state.strain_symbol;
    const declKlass =
      declSym === "♥" || declSym === "♦" ? "suit-red" :
      declSym === "♠" || declSym === "♣" ? "suit-black" : "";
    const made = r.declarer_tricks >= state.tricks_needed;
    const main = el("div", { class: "result-big" });
    main.appendChild(document.createTextNode(state.level + ""));
    main.appendChild(el("span", { class: declKlass }, declSym));
    main.appendChild(document.createTextNode(
      `   ${made ? "made" : "down"} ${made ? r.declarer_tricks : (state.tricks_needed - r.declarer_tricks)}   (${r.result_str})`
    ));
    center.appendChild(main);
    return;
  }
  let trickLabel = `Trick ${Math.min(state.trick_number, 13)}`;
  if (!state.user_to_play && state.to_play) trickLabel += ` · ${state.to_play} to play…`;
  if (hasHistory) trickLabel += " · click to see last";
  center.appendChild(el("div", { class: "center-trick-label" }, trickLabel));
  for (const p of state.current_trick) {
    const c = p.card;
    const symbol = c[0];
    const suitKlass = (symbol === "♥" || symbol === "♦") ? "suit-red" : "suit-black";
    const pos = seatToPosition[p.seat];
    const posKlass = pos ? `center-trick-${pos}` : "";
    center.appendChild(el("div", { class: `trick-card ${suitKlass} ${posKlass}` }, c));
  }
}

function renderTrickSummary(state) {
  const div = document.getElementById("trick-summary");
  const ns = state.tricks_taken.NS;
  const ew = state.tricks_taken.EW;
  const need = state.tricks_needed;
  const declarerSide = (state.declarer === "N" || state.declarer === "S") ? "NS" : "EW";
  const declarerHas = declarerSide === "NS" ? ns : ew;
  div.textContent = `Tricks: NS ${ns} · EW ${ew}   (${state.declarer} needs ${need}; has ${declarerHas})`;
}

function renderResult(state) {
  // Result is now drawn into the center of the table by renderTable, and the
  // four hands appear in their seat slots by renderSeatInto. The bottom panel
  // stays hidden.
  document.getElementById("result-panel").hidden = true;
}

function render(state) {
  lastState = state;
  document.getElementById("status-line").textContent =
    `${state.scenario} · Deal ${state.board_num} · ${state.contract_str}`;
  document.getElementById("game").hidden = false;
  document.getElementById("claim-btn").disabled = state.complete;
  document.getElementById("undo-btn").disabled = !state.can_undo;
  renderAuction(state);
  renderContractDisplay(state);
  renderTable(state);
  renderTricksStrip(state);
  renderTrickSummary(state);
  renderResult(state);
  updateInferenceUI(state);
}

// ---------- actions ----------

let currentScenario = null;

async function loadMenu() {
  const data = await api("/api/menu");
  const menu = document.getElementById("menu");
  menu.innerHTML = "";
  for (const sec of data.sections) {
    const section = el("div", { class: "menu-section" });
    const header = el("div", { class: "menu-section-header" });
    header.appendChild(el("span", {}, sec.title));
    header.appendChild(el("span", { class: "chevron" }, "▶"));
    header.addEventListener("click", () => section.classList.toggle("open"));
    section.appendChild(header);

    const list = el("div", { class: "menu-scenarios" });
    for (const name of sec.scenarios) {
      const btn = el("button", {
        class: "menu-scenario-btn",
        "data-scenario": name,
        onclick: () => onScenarioClick(name, btn),
      }, name.replaceAll("_", " "));
      list.appendChild(btn);
    }
    section.appendChild(list);
    menu.appendChild(section);
  }
}

function highlightActiveScenario(name) {
  for (const b of document.querySelectorAll(".menu-scenario-btn")) {
    b.classList.toggle("active", b.getAttribute("data-scenario") === name);
  }
}

function applyMenuFilter(query) {
  const q = query.trim().toLowerCase();
  for (const section of document.querySelectorAll(".menu-section")) {
    let visibleCount = 0;
    for (const btn of section.querySelectorAll(".menu-scenario-btn")) {
      const name = (btn.getAttribute("data-scenario") || "").toLowerCase();
      const label = btn.textContent.toLowerCase();
      const match = !q || name.includes(q) || label.includes(q);
      btn.classList.toggle("hidden", !match);
      if (match) visibleCount += 1;
    }
    section.classList.toggle("hidden", visibleCount === 0);
    // Auto-open sections during an active search so matches are visible.
    if (q && visibleCount > 0) section.classList.add("open");
  }
}

async function onScenarioClick(name) {
  currentScenario = name;
  highlightActiveScenario(name);
  // When the user clicks a new scenario, reset board index to 0 and start.
  document.getElementById("board-index").value = "0";
  await startSession();
}

async function startSession() {
  if (!currentScenario) return;
  const boardIndex = parseInt(document.getElementById("board-index").value, 10) || 0;
  const role = document.getElementById("role-select").value || "declarer";
  try {
    const data = await api("/api/session", {
      method: "POST",
      body: JSON.stringify({ scenario: currentScenario, board_index: boardIndex, role }),
    });
    sessionId = data.session_id;
    if (data.board_index != null) {
      document.getElementById("board-index").value = String(data.board_index);
    }
    groundTruth = null;
    inferenceHandledForTrick = -1;
    inferenceOpenedManually = false;
    coachingFiredTriggers = new Set();
    coachingTips = [];
    coachingPending = false;
    document.getElementById("inference-panel").hidden = true;
    document.getElementById("feedback-panel").hidden = true;
    document.getElementById("result-panel").hidden = true;
    syncSidebarVisibility();
    document.getElementById("next-deal-btn").disabled = false;
    document.getElementById("claim-btn").disabled = false;
    document.getElementById("replay-btn").disabled = false;
    document.getElementById("review-btn").disabled = false;
    document.getElementById("picker-hint").textContent = "";
    viewingLastTrick = false;
    trickFreeze = null;
    awaitingPlay = false;
    render(data.state);
    animateAuction(data.state);
  } catch (e) {
    alert("Could not start session: " + e.message);
  }
}

async function playCard(suit, rank) {
  if (!sessionId || trickFreeze) return;
  try {
    const data = await api(`/api/session/${sessionId}/play`, {
      method: "POST",
      body: JSON.stringify({ suit, rank }),
    });
    await advanceWithTrickHold(data.state);
  } catch (e) {
    alert("Couldn't play card: " + e.message);
  }
}

// If the new state completes a trick, show the four cards in their seats for
// TRICK_HOLD_MS before letting the trick collapse to the next one.
async function advanceWithTrickHold(newState) {
  const oldLen = (lastState && lastState.trick_history && lastState.trick_history.length) || 0;
  const newLen = (newState.trick_history || []).length;
  if (newLen > oldLen) {
    trickFreeze = newState.trick_history[newLen - 1];
    render(newState);
    await sleep(TRICK_HOLD_MS);
    trickFreeze = null;
  }
  render(newState);
}

async function nextDeal() {
  if (!currentScenario) return;
  const cur = parseInt(document.getElementById("board-index").value, 10) || 0;
  document.getElementById("board-index").value = String(cur + 1);
  await startSession();
}

async function claimRest() {
  if (!sessionId) return;
  try {
    const data = await api(`/api/session/${sessionId}/claim`, { method: "POST" });
    render(data.state);
  } catch (e) {
    alert("Couldn't claim: " + e.message);
  }
}

function animateAuction(state) {
  // No timed reveal — show the full auction immediately in the centre of the
  // table and wait for the user to click Play.
  auctionAnimationToken += 1;
  auctionAnimating = false;
  auctionVisibleCount = null;
  awaitingPlay = (state.auction || []).length > 0;
  render(lastState);
}

async function startPlay() {
  awaitingPlay = false;
  auctionVisibleCount = null;
  // First render closes the auction overlay and gives end-of-auction
  // coaching a chance to fire while cards_played_count is still 0.
  if (lastState) render(lastState);
  // Then ask the server to play any non-user seats (e.g., LHO's opening
  // lead) until it's the user's turn. No-op for the leader role.
  if (sessionId) {
    try {
      const data = await api(`/api/session/${sessionId}/start-play`, { method: "POST" });
      render(data.state);
    } catch (e) {
      console.warn("start-play failed:", e);
    }
  }
}

function startReview() {
  if (!lastState) return;
  reviewingAuction = true;
  render(lastState);
}

function endReview() {
  if (!reviewingAuction) return;
  reviewingAuction = false;
  if (lastState) render(lastState);
}

async function replayDeal() {
  if (!sessionId || trickFreeze) return;
  try {
    const data = await api(`/api/session/${sessionId}/replay`, { method: "POST" });
    viewingLastTrick = false;
    trickFreeze = null;
    render(data.state);
  } catch (e) {
    alert("Couldn't replay: " + e.message);
  }
}

async function undoLast() {
  if (!sessionId || trickFreeze) return;
  try {
    const data = await api(`/api/session/${sessionId}/undo`, { method: "POST" });
    viewingLastTrick = false;
    render(data.state);
  } catch (e) {
    alert("Couldn't undo: " + e.message);
  }
}

// ---------- Claude grading ----------

const PREFS_KEY = "bridgePlayTrainer.prefs.v1";
const CLAUDE_MODEL = "claude-opus-4-7";
const STRUCTURED_FROM_TRICK = 4;
const HCP = { A: 4, K: 3, Q: 2, J: 1 };
const SUIT_SYMBOL_FROM_CHAR = { "♠": "S", "♥": "H", "♦": "D", "♣": "C" };

let groundTruth = null;
let inferenceHandledForTrick = -1;
let inferenceOpenedManually = false;

// Coaching mode (slice 1: end-of-auction + opening-lead).
let coachingFiredTriggers = new Set();   // Set<string>: which triggers have already fired this deal
let coachingTips = [];                   // Array<{trigger, label, text}> — accumulates across the deal so the user can scroll back
let coachingPending = false;             // True while a Claude call is in flight

function getPrefs() {
  try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; }
  catch { return {}; }
}
function setPrefs(patch) {
  localStorage.setItem(PREFS_KEY, JSON.stringify({ ...getPrefs(), ...patch }));
}
function clearPref(key) {
  const p = getPrefs(); delete p[key];
  localStorage.setItem(PREFS_KEY, JSON.stringify(p));
}
function gradingEnabled() { return !!getPrefs().gradingEnabled; }
function gradingTrigger() { return getPrefs().gradingTrigger || "trick4"; }
function gradingKey() { return getPrefs().anthropicKey || ""; }
function gradingMode() { return getPrefs().gradingMode || "testing"; }
function isCoaching() { return gradingMode() === "coaching"; }

// --- settings modal ---

function openSettings() {
  document.getElementById("settings-grading-enabled").checked = gradingEnabled();
  document.getElementById("settings-mode").value = gradingMode();
  document.getElementById("settings-trigger").value = gradingTrigger();
  document.getElementById("settings-trigger-row").style.display =
    gradingMode() === "coaching" ? "none" : "";
  syncKeyStatus();
  document.getElementById("settings-modal").hidden = false;
}
function closeSettings() {
  setPrefs({
    gradingEnabled: document.getElementById("settings-grading-enabled").checked,
    gradingMode: document.getElementById("settings-mode").value,
    gradingTrigger: document.getElementById("settings-trigger").value,
  });
  document.getElementById("settings-modal").hidden = true;
  if (lastState) updateInferenceUI(lastState);
}
function syncKeyStatus() {
  const key = gradingKey();
  const status = document.getElementById("settings-key-status");
  const removeBtn = document.getElementById("settings-key-remove");
  if (key) {
    status.textContent = `set (…${key.slice(-4)})`;
    removeBtn.hidden = false;
  } else {
    status.textContent = "not set";
    removeBtn.hidden = true;
  }
}
function removeKey() {
  if (!confirm("Remove your Anthropic API key from this browser?")) return;
  clearPref("anthropicKey");
  syncKeyStatus();
}

// --- key wizard ---

function openWizard() {
  document.getElementById("settings-modal").hidden = true;
  document.getElementById("wizard-modal").hidden = false;
  showWizardStep(1);
  document.getElementById("wizard-key-input").value = "";
  const status = document.getElementById("wizard-test-status");
  status.textContent = "";
  status.className = "muted";
}
function closeWizard() {
  document.getElementById("wizard-modal").hidden = true;
}
function showWizardStep(n) {
  const steps = document.querySelectorAll(".wizard-step");
  steps.forEach((s, i) => { s.hidden = ((i + 1) !== n); });
}
function wizardStepCount() {
  return document.querySelectorAll(".wizard-step").length;
}
async function testAndSaveKey() {
  const key = document.getElementById("wizard-key-input").value.trim();
  const status = document.getElementById("wizard-test-status");
  if (!key.startsWith("sk-ant-")) {
    status.textContent = "That doesn't look right — the key should start with sk-ant-.";
    status.className = "err";
    return;
  }
  status.textContent = "Testing…";
  status.className = "muted";
  const testBtn = document.getElementById("wizard-test-btn");
  testBtn.disabled = true;
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 1,
        messages: [{ role: "user", content: "ok" }],
      }),
    });
    if (!r.ok) {
      const txt = await r.text();
      status.textContent = `Key didn't work (${r.status}). ${txt.slice(0, 120)}`;
      status.className = "err";
      return;
    }
    setPrefs({ anthropicKey: key, gradingEnabled: true });
    syncKeyStatus();
    showWizardStep(wizardStepCount());
  } catch (e) {
    status.textContent = `Test failed: ${e.message}`;
    status.className = "err";
  } finally {
    testBtn.disabled = false;
  }
}

// --- bridge math helpers (browser side) ---

function handHcp(hand) {
  let n = 0;
  for (const s of "SHDC") for (const r of hand[s]) n += HCP[r] || 0;
  return n;
}
function handLengths(hand) {
  return { S: hand.S.length, H: hand.H.length, D: hand.D.length, C: hand.C.length };
}
function formatHand(hand) {
  return `♠${hand.S.join("") || "-"} ♥${hand.H.join("") || "-"} ♦${hand.D.join("") || "-"} ♣${hand.C.join("") || "-"}`;
}
function seatLabel(seat, state) {
  if (seat === state.declarer) return `Declarer (${seat})`;
  if (seat === state.dummy) return `Dummy (${seat})`;
  return `Defender (${seat})`;
}

// --- ground truth fetch ---

async function ensureGroundTruth() {
  if (groundTruth || !sessionId) return groundTruth;
  groundTruth = await api(`/api/session/${sessionId}/ground-truth`);
  return groundTruth;
}

// --- inference panel state machine ---

function inferenceAllowed(state) {
  if (!gradingEnabled() || !gradingKey()) return false;
  if (state.complete) return false;
  if (bidsInCenter() || trickFreeze) return false;
  const completed = (state.trick_history || []).length;
  return completed >= 1;
}

function inferenceAutoTriggered(state) {
  if (!inferenceAllowed(state)) return false;
  const trigger = gradingTrigger();
  if (trigger === "manual") return false;
  const completed = (state.trick_history || []).length;
  if (trigger === "every") return completed >= 1 && completed < 13;
  if (trigger === "trick4") return completed >= 3 && completed < 13;
  return false;
}

function inferenceInputMode(state) {
  const completed = (state.trick_history || []).length;
  return completed >= STRUCTURED_FROM_TRICK ? "structured" : "free";
}

function syncSidebarVisibility() {
  const infVis = !document.getElementById("inference-panel").hidden;
  const fbVis = !document.getElementById("feedback-panel").hidden;
  document.getElementById("sidebar").hidden = (infVis || fbVis);
}

async function updateInferenceUI(state) {
  const panel = document.getElementById("inference-panel");
  const gradeBtn = document.getElementById("grade-now-btn");

  // Coaching mode: fire pre-lead / opening-lead triggers, keep the panel
  // visible while a tip is showing or being fetched.
  if (isCoaching()) {
    gradeBtn.hidden = true;
    // If a Claude call is in flight, leave the panel as-is (the runner
    // will re-render when it returns).
    if (coachingPending) {
      syncSidebarVisibility();
      return;
    }
    const trig = pendingCoachingTrigger(state);
    if (trig) {
      runCoachingTip(trig, state);
      return;
    }
    // No new trigger pending; keep the panel visible if we have tips so
    // the student can still scroll through earlier coaching.
    if (coachingTips.length > 0) {
      renderCoachingPanel();
    } else {
      panel.hidden = true;
      syncSidebarVisibility();
    }
    return;
  }

  const allowed = inferenceAllowed(state);
  // Manual-trigger Grade button: visible only in manual mode while allowed.
  if (allowed && gradingTrigger() === "manual") {
    gradeBtn.hidden = false;
    gradeBtn.disabled = false;
  } else {
    gradeBtn.hidden = true;
  }

  const completed = (state.trick_history || []).length;
  const autoOpen = inferenceAutoTriggered(state) && inferenceHandledForTrick < completed;
  const shouldShow = autoOpen || inferenceOpenedManually;
  if (!shouldShow) {
    panel.hidden = true;
    syncSidebarVisibility();
    return;
  }
  try {
    await ensureGroundTruth();
  } catch (e) {
    panel.hidden = true;
    syncSidebarVisibility();
    return;
  }
  panel.hidden = false;
  renderInferenceBody(state);
  syncSidebarVisibility();
}

function renderInferenceBody(state) {
  const body = document.getElementById("inference-body");
  body.innerHTML = "";
  const completed = (state.trick_history || []).length;
  const labels = (groundTruth.hidden_labels || []).join(" and ");
  body.appendChild(el("div", { class: "prompt-line" },
    `After ${completed} trick${completed === 1 ? "" : "s"} — your read on ${labels}.`));

  const mode = inferenceInputMode(state);
  if (mode === "free") {
    body.appendChild(el("textarea", {
      id: "infer-textarea",
      placeholder: "e.g. West has ♥KQJ; East 2-3 spades, 8-10 HCP.",
    }));
  } else {
    const rem = computeRemainingFromState(state);
    body.appendChild(el("div", { class: "muted" },
      `Hidden cards left: ♠${rem.suits.S} ♥${rem.suits.H} ♦${rem.suits.D} ♣${rem.suits.C}  ·  HCP unseen: ${rem.hcp}`));
    for (let i = 0; i < groundTruth.hidden_seats.length; i++) {
      const seat = groundTruth.hidden_seats[i];
      const label = groundTruth.hidden_labels[i];
      const block = el("div", { class: "struct-block" });
      block.appendChild(el("div", { class: "struct-block-title" }, `Your read on ${label}`));
      for (const suit of ["S", "H", "D", "C"]) {
        const row = el("div", { class: "struct-row" });
        const lbl = el("label", {});
        lbl.appendChild(el("span", { class: suitClass(suit) }, SUIT_SYMBOL[suit]));
        lbl.appendChild(document.createTextNode(" length:"));
        row.appendChild(lbl);
        row.appendChild(el("input", {
          type: "number", min: "0", max: "13",
          "data-seat": seat, "data-field": `len-${suit}`,
        }));
        block.appendChild(row);
      }
      const hcpRow = el("div", { class: "struct-row" });
      hcpRow.appendChild(el("label", {}, "HCP estimate:"));
      hcpRow.appendChild(el("input", {
        type: "number", min: "0", max: "40",
        "data-seat": seat, "data-field": "hcp",
      }));
      block.appendChild(hcpRow);
      body.appendChild(block);
    }
  }
  document.getElementById("inference-status").textContent = "";
}

function computeRemainingFromState(state) {
  const suits = { S: 0, H: 0, D: 0, C: 0 };
  let hcp = 0;
  for (const seat of groundTruth.hidden_seats) {
    const init = groundTruth.initial_hands[seat];
    const played = state.cards_played_by_seat[seat] || [];
    const playedSet = new Set();
    for (const cd of played) {
      const suit = SUIT_SYMBOL_FROM_CHAR[cd[0]];
      const rank = cd.slice(1);
      playedSet.add(`${suit}${rank}`);
    }
    for (const suit of "SHDC") {
      for (const rank of init[suit]) {
        if (!playedSet.has(`${suit}${rank}`)) {
          suits[suit] += 1;
          hcp += HCP[rank] || 0;
        }
      }
    }
  }
  return { suits, hcp };
}

function collectStructuredEstimate() {
  const est = {};
  for (const seat of groundTruth.hidden_seats) {
    est[seat] = { lengths: { S: 0, H: 0, D: 0, C: 0 }, hcp: 0 };
    for (const suit of "SHDC") {
      const input = document.querySelector(`[data-seat="${seat}"][data-field="len-${suit}"]`);
      est[seat].lengths[suit] = parseInt(input?.value || "0", 10);
    }
    const hcpInput = document.querySelector(`[data-seat="${seat}"][data-field="hcp"]`);
    est[seat].hcp = parseInt(hcpInput?.value || "0", 10);
  }
  return est;
}

// --- payload builders (mirror pipe5) ---

function visibleSeats() {
  const hidden = new Set(groundTruth.hidden_seats);
  return ["N", "E", "S", "W"].filter(s => !hidden.has(s));
}

function commonBlocks(state) {
  const visBlock = visibleSeats()
    .map(s => `${seatLabel(s, state)}: ${formatHand(groundTruth.initial_hands[s])}`)
    .join("\n");
  const hidBlock = groundTruth.hidden_seats
    .map(s => `${s}: ${formatHand(groundTruth.initial_hands[s])}`)
    .join("\n");
  const auctionLine = (state.auction || []).map(c => `${c.seat}:${c.call}`).join(" ");
  const completed = (state.trick_history || []).length;
  const tricksTxt = (state.trick_history || []).map(t =>
    `Trick ${t.n}: led by ${t.leader} — ${t.plays.map(p => `${p.seat}:${p.card}`).join(", ")}  won by ${t.winner}`
  ).join("\n") || "(none)";
  return { visBlock, hidBlock, auctionLine, completed, tricksTxt };
}

function buildFreePayload(state, userText) {
  const { visBlock, hidBlock, auctionLine, completed, tricksTxt } = commonBlocks(state);
  return `## Auction
Dealer: ${state.dealer}
${auctionLine}
Final contract: ${state.contract_str}

## Role
${groundTruth.role_desc}

## Visible to student
${visBlock}

## Hidden (ground truth — NOT shown to student)
${hidBlock}

## Play so far (${completed} tricks)
${tricksTxt}

## Student's prose estimate
${userText}

Return JSON only.`;
}

function buildStructuredPayload(state, est) {
  const { visBlock, hidBlock, auctionLine, completed, tricksTxt } = commonBlocks(state);
  const studentLines = Object.entries(est).map(([s, v]) =>
    `${s}: ♠${v.lengths.S} ♥${v.lengths.H} ♦${v.lengths.D} ♣${v.lengths.C}   HCP=${v.hcp}`
  ).join("\n");
  const actualLines = groundTruth.hidden_seats.map(s => {
    const l = handLengths(groundTruth.initial_hands[s]);
    return `${s}: ♠${l.S} ♥${l.H} ♦${l.D} ♣${l.C}   HCP=${handHcp(groundTruth.initial_hands[s])}`;
  }).join("\n");
  return `## Auction
Dealer: ${state.dealer}
${auctionLine}
Final contract: ${state.contract_str}

## Role
${groundTruth.role_desc}

## Visible to student
${visBlock}

## Ground truth for the hidden hands (NOT shown to student)
${actualLines}
${hidBlock}

## Play so far (${completed} tricks)
${tricksTxt}

## Student's structured estimate
${studentLines}

Grade each length and HCP separately. Return JSON only.`;
}

const SEAT_PERSPECTIVE = `The seat letters in the payload use the student's rotated view: S = the student (always bottom of the table), N = partner, W = LHO (left-hand opponent), E = RHO (right-hand opponent). When you write claims, notes, hints, or any narrative text, refer to the seats from the student's perspective using "you", "partner", "LHO", and "RHO" — not the raw letters. The JSON "claim" field for structured grading may still use the letters S/N/E/W for compactness, but every other field aimed at the student should use the perspective labels.`;

const FREE_SYSTEM_PROMPT = `You are a bridge instructor grading a student's free-text read on the hidden hands during a deal.

You receive: the auction, the hands visible to the student, the cards played so far, the ACTUAL hidden hands (ground truth — known only to you), and the student's prose estimate.

Grade the student's stated claims against ground truth AND against what was inferrable from the visible evidence.

${SEAT_PERSPECTIVE}

Return JSON only:
{
  "facets": [{"claim": "...", "verdict": "correct|partial|missed|wrong", "note": "<one sentence>"}],
  "missed_inferences": ["..."],
  "next_trick_hint": "...",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}`;

const STRUCTURED_SYSTEM_PROMPT = `You are a bridge instructor grading a student's structured read on hidden hands.

You receive: the auction, visible hands, play history, ACTUAL hidden hands (ground truth), and the student's per-hand suit-lengths + HCP estimates.

For EACH hidden hand, grade each suit-length and HCP separately:
- length exact = correct, ±1 = partial, ±2+ = wrong
- HCP within ±1 = correct, within ±3 = partial, ±4+ = wrong

${SEAT_PERSPECTIVE}

Return JSON only:
{
  "facets": [{"claim": "<who> <suit/HCP> = <student> (actual: <truth>)", "verdict": "...", "note": "..."}],
  "reasoning_notes": ["<short observations on WHY the actual hand was inferrable>"],
  "next_trick_hint": "...",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}`;

// ---- Coaching mode prompts ----

const COACH_END_OF_AUCTION_PROMPT = `You are a friendly bridge coach. The auction has just concluded. **The opening lead has NOT been made yet — do not discuss the lead at all.**

${SEAT_PERSPECTIVE}

**ACCURACY**: be conservative and double-dummy-aware. Assume opponents play their honors optimally. Examples of common errors to avoid:
- Dummy holding ♣KQ doubleton opposite opp ♣Axx typically establishes ONE trick after the ace falls, not two — the ace claims one of your K/Q.
- "Finesse for the K" promises a 50% trick, not a sure one; don't count it as guaranteed in the Tricks card.
- A 5-card side suit only yields length tricks AFTER you've drawn opp trumps / set the suit up, and only if the split is favorable.

Cover three angles, tailored to the student's role:
- **Tricks available**: how many SURE tricks the student's side has now, given the visible hand (and dummy if declarer). No finesses, no favorable splits.
- **Promotion opportunities**: which cards in the visible hand CAN grow into winners (length tricks, honor sequences, finesse positions, suit establishment) — be specific about the assumption ("if the ♠Q is onside", "if hearts split 3-2").
- **Risks to watch for**: what the opponents might do — bad splits, opp honors located by the bidding, fast losers in side suits.

Return ONLY a JSON object with three string fields, each one short sentence (under 30 words):
{"tricks": "...", "promotion": "...", "risks": "..."}

No prose outside the JSON. No bullets inside the strings. Refer to seats with "you / partner / LHO / RHO".`;

const COACH_OPENING_LEAD_PROMPT = `You are a friendly bridge coach. The opening lead has just been made. Dummy is now face-up.

${SEAT_PERSPECTIVE}

One short observation only — pick whichever is most useful given the student's role: what the lead reveals about leader's hand, what dummy adds to the picture, or one tactical point to plan for now.

**Keep it tiny: ONE short sentence, no more than 25 words.** Plain prose, no JSON, no bullets.`;

function buildCoachingPayload(state, triggerKey) {
  const { visBlock, hidBlock, auctionLine, completed, tricksTxt } = commonBlocks(state);
  const stage = triggerKey === "endOfAuction" ? "auction just concluded, no card played yet" : "right after the opening lead";
  const partialTrick = (state.current_trick || [])
    .map(p => `${p.seat}:${p.card}`).join(", ") || "(none yet)";
  return `## Auction
Dealer: ${state.dealer}
${auctionLine}
Final contract: ${state.contract_str}

## Role
${groundTruth.role_desc}

## Stage
${stage}.

## Visible to student
${visBlock}

## Hidden (ground truth — NOT shown to student in the panel; available to you for accurate guidance)
${hidBlock}

## Play so far (${completed} completed tricks)
${tricksTxt}

## Cards in the current (in-progress) trick
${partialTrick}

Respond with plain prose for the student. No JSON.`;
}

async function callClaudeCoach(system, userText) {
  const key = gradingKey();
  if (!key) throw new Error("no API key configured");
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: CLAUDE_MODEL,
      max_tokens: 800,
      system,
      messages: [{ role: "user", content: userText }],
    }),
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`Anthropic ${r.status}: ${txt.slice(0, 200)}`);
  }
  const data = await r.json();
  return (data.content || []).map(b => b.type === "text" ? b.text : "").join("").trim();
}

function pendingCoachingTrigger(state) {
  if (!isCoaching() || !gradingEnabled() || !gradingKey()) return null;
  if (bidsInCenter() || trickFreeze) return null;
  // End of play: deal is complete. Fires once per deal.
  if (state.complete) {
    if (!coachingFiredTriggers.has("endOfPlay")) return "endOfPlay";
    return null;
  }
  const tricksDone = (state.trick_history || []).length;
  const currentCards = (state.current_trick || []).length;
  // End-of-auction: no cards on the table yet. Fires for every role
  // (declarer + both defenders) once per deal.
  if (tricksDone === 0 && currentCards === 0
      && !coachingFiredTriggers.has("endOfAuction")) {
    return "endOfAuction";
  }
  // Opening lead: exactly one card has hit the table (either still in
  // trick 1 or trick 1 just completed).
  const openingPlayed = (tricksDone === 0 && currentCards === 1)
                     || (tricksDone === 1 && currentCards === 0);
  if (openingPlayed && !coachingFiredTriggers.has("openingLead")) {
    return "openingLead";
  }
  return null;
}

const COACH_LABEL = {
  endOfAuction: "End of auction",
  openingLead: "After the opening lead",
  endOfPlay: "End of play",
};

const COACH_END_OF_PLAY_PROMPT = `You are a friendly bridge coach. The deal is complete. You can now see every card and the full play record.

${SEAT_PERSPECTIVE}

Audit the student's plays (in declarer mode the student plays you AND your partner / dummy; in defender mode the student plays only their seat). Compare against ideal double-dummy play.

Categorize the plays:
- **errors**: card choices that clearly gave up a trick the student's side should have won — concrete: "at trick N you played the ♣Q when the ♣J wins the trick cheaper" etc.
- **suboptimal**: technically less than double-dummy but didn't cost a trick on this deal (still worth pointing out so the habit doesn't bite later).
- **summary**: one short sentence comparing the contract result to what was makeable with double-dummy play — and one positive note if there's something to praise.

Return ONLY a JSON object with three string fields, each at most two short sentences:
{"errors": "...", "suboptimal": "...", "summary": "..."}

If there are no errors, set "errors" to "(no clear errors — well played)". Same convention for "suboptimal". Refer to seats with "you / partner / LHO / RHO".`;

function parseJsonFromClaude(text) {
  let t = text.trim();
  if (t.startsWith("```")) {
    // Strip ```json ... ``` fences.
    t = t.replace(/^```(?:json)?\s*/i, "").replace(/```\s*$/, "").trim();
  }
  return JSON.parse(t);
}

async function runCoachingTip(triggerKey, state) {
  coachingFiredTriggers.add(triggerKey);
  coachingPending = true;
  renderCoachingPanel();
  try {
    await ensureGroundTruth();
    const system = triggerKey === "endOfAuction" ? COACH_END_OF_AUCTION_PROMPT
                 : triggerKey === "endOfPlay"   ? COACH_END_OF_PLAY_PROMPT
                 :                                COACH_OPENING_LEAD_PROMPT;
    const payload = buildCoachingPayload(state, triggerKey);
    const text = await callClaudeCoach(system, payload);
    if (triggerKey === "endOfAuction") {
      const obj = parseJsonFromClaude(text);
      coachingTips.push({ trigger: triggerKey, label: "End of auction · Tricks",    text: obj.tricks    || "(no response)" });
      coachingTips.push({ trigger: triggerKey, label: "End of auction · Promotion", text: obj.promotion || "(no response)" });
      coachingTips.push({ trigger: triggerKey, label: "End of auction · Risks",     text: obj.risks     || "(no response)" });
    } else if (triggerKey === "endOfPlay") {
      const obj = parseJsonFromClaude(text);
      coachingTips.push({ trigger: triggerKey, label: "End of play · Clear errors", text: obj.errors     || "(no response)" });
      coachingTips.push({ trigger: triggerKey, label: "End of play · Suboptimal",   text: obj.suboptimal || "(no response)" });
      coachingTips.push({ trigger: triggerKey, label: "End of play · Result",       text: obj.summary    || "(no response)" });
    } else {
      coachingTips.push({ trigger: triggerKey, label: COACH_LABEL[triggerKey], text });
    }
  } catch (e) {
    coachingTips.push({ trigger: triggerKey, label: COACH_LABEL[triggerKey] + " (error)", text: `Could not fetch coaching tip: ${e.message}` });
  } finally {
    coachingPending = false;
    renderCoachingPanel();
    // Chain to the next trigger if the state has advanced while we were
    // waiting on Claude (e.g., opening lead got played after end-of-auction).
    if (lastState) {
      const next = pendingCoachingTrigger(lastState);
      if (next) runCoachingTip(next, lastState);
    }
  }
}

function renderCoachingPanel() {
  const panel = document.getElementById("inference-panel");
  const title = document.getElementById("inference-title");
  const body = document.getElementById("inference-body");
  const submit = document.getElementById("inference-submit");
  const skip = document.getElementById("inference-skip");
  const hint = document.getElementById("inference-hint");
  const hintBody = document.getElementById("inference-hint-body");
  panel.hidden = false;
  title.textContent = "Coaching · scroll up to revisit";
  body.innerHTML = "";
  body.classList.add("coaching-tips-list");
  for (const tip of coachingTips) {
    const card = el("div", { class: "coach-tip-card" });
    card.appendChild(el("div", { class: "coach-tip-label" }, tip.label));
    card.appendChild(el("div", { class: "coach-tip-text" }, tip.text));
    body.appendChild(card);
  }
  if (coachingPending) {
    body.appendChild(el("div", { class: "coach-tip-card coach-loading" }, "Thinking…"));
  }
  // Auto-scroll to the newest tip but leave older ones reachable above.
  body.scrollTop = body.scrollHeight;
  // Hide testing-mode buttons and any leftover Continue button.
  submit.hidden = true;
  skip.hidden = true;
  hint.hidden = true;
  hintBody.hidden = true;
  const cont = document.getElementById("coach-continue-btn");
  if (cont) cont.remove();
  syncSidebarVisibility();
}

async function callClaude(system, userText) {
  const key = gradingKey();
  if (!key) throw new Error("no API key configured");
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: CLAUDE_MODEL,
      max_tokens: 1500,
      system,
      messages: [{ role: "user", content: userText }],
    }),
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`Anthropic ${r.status}: ${txt.slice(0, 200)}`);
  }
  const data = await r.json();
  let text = (data.content || []).map(b => b.type === "text" ? b.text : "").join("").trim();
  if (text.startsWith("```")) {
    text = text.split("```")[1] || "";
    if (text.toLowerCase().startsWith("json")) text = text.split("\n").slice(1).join("\n");
    text = text.split("```")[0];
  }
  return JSON.parse(text);
}

async function submitInference() {
  const state = lastState;
  if (!state) return;
  const status = document.getElementById("inference-status");
  status.className = "muted";
  status.textContent = "Asking Claude…";
  const submitBtn = document.getElementById("inference-submit");
  submitBtn.disabled = true;
  try {
    const mode = inferenceInputMode(state);
    let payload, system;
    if (mode === "free") {
      const text = document.getElementById("infer-textarea").value.trim();
      if (!text) {
        status.textContent = "Type something first.";
        status.className = "err";
        return;
      }
      payload = buildFreePayload(state, text);
      system = FREE_SYSTEM_PROMPT;
    } else {
      const est = collectStructuredEstimate();
      payload = buildStructuredPayload(state, est);
      system = STRUCTURED_SYSTEM_PROMPT;
    }
    const result = await callClaude(system, payload);
    renderFeedback(result);
    inferenceHandledForTrick = (state.trick_history || []).length;
    inferenceOpenedManually = false;
    document.getElementById("inference-panel").hidden = true;
    syncSidebarVisibility();
    status.textContent = "";
  } catch (e) {
    status.textContent = "Grading failed: " + e.message;
    status.className = "err";
  } finally {
    submitBtn.disabled = false;
  }
}

function skipInference() {
  const state = lastState;
  inferenceHandledForTrick = state ? (state.trick_history || []).length : -1;
  inferenceOpenedManually = false;
  document.getElementById("inference-panel").hidden = true;
  syncSidebarVisibility();
}

function openInferenceManually() {
  inferenceOpenedManually = true;
  if (lastState) updateInferenceUI(lastState);
}

function toggleHint() {
  const div = document.getElementById("inference-hint-body");
  if (div.hidden) {
    renderHintBody();
    div.hidden = false;
  } else {
    div.hidden = true;
  }
}

function renderHintBody() {
  const div = document.getElementById("inference-hint-body");
  div.innerHTML = "";
  const state = lastState;
  if (!state) return;

  if (state.auction && state.auction.length) {
    div.appendChild(el("div", { class: "hint-section-title" }, "Auction"));
    const grid = el("div", { class: "center-auction-grid hint-auction-grid" });
    fillAuctionGrid(grid, state);
    div.appendChild(grid);
  }

  div.appendChild(el("div", { class: "hint-section-title" }, "Tricks"));
  const history = state.trick_history || [];
  if (history.length === 0) {
    div.appendChild(el("div", { class: "muted" }, "(no tricks played yet)"));
    return;
  }
  for (const t of history) {
    const row = el("div", { class: "hint-trick-row" });
    row.appendChild(el("span", { class: "hint-trick-num" }, `T${t.n}`));
    row.appendChild(document.createTextNode(" "));
    t.plays.forEach((p, i) => {
      row.appendChild(el("span", { class: "hint-play-seat" }, `${p.seat}:`));
      const sym = p.card[0];
      const klass = (sym === "♥" || sym === "♦") ? "suit-red" : "suit-black";
      row.appendChild(el("span", { class: klass }, p.card));
      if (i < t.plays.length - 1) row.appendChild(document.createTextNode("  "));
    });
    row.appendChild(document.createTextNode(`  → ${t.winner}`));
    div.appendChild(row);
  }
}

const VERDICT_ICON = { correct: "✅", partial: "⚠️", missed: "❌", wrong: "❌" };

function renderFeedback(ev) {
  const panel = document.getElementById("feedback-panel");
  const body = document.getElementById("feedback-body");
  body.innerHTML = "";
  panel.hidden = false;
  syncSidebarVisibility();
  const score = (typeof ev.score === "number") ? ev.score.toFixed(2) : "?";
  body.appendChild(el("div", { class: "feedback-overall" },
    `Overall: ${String(ev.overall || "?").toUpperCase()}   (score ${score})`));
  for (const f of (ev.facets || [])) {
    const row = el("div", { class: "feedback-row" });
    row.appendChild(el("span", { class: "verdict-icon" }, VERDICT_ICON[f.verdict] || "•"));
    row.appendChild(el("span", {}, `${f.claim || ""} — ${f.note || ""}`));
    body.appendChild(row);
  }
  for (const r of (ev.reasoning_notes || [])) {
    const row = el("div", { class: "feedback-row" });
    row.appendChild(el("span", { class: "verdict-icon" }, "💡"));
    row.appendChild(el("span", {}, r));
    body.appendChild(row);
  }
  for (const m of (ev.missed_inferences || [])) {
    const row = el("div", { class: "feedback-row" });
    row.appendChild(el("span", { class: "verdict-icon" }, "❌"));
    row.appendChild(el("span", {}, `MISSED: ${m}`));
    body.appendChild(row);
  }
  if (ev.next_trick_hint) {
    body.appendChild(el("div", { class: "feedback-hint" },
      `🎯 Next trick: ${ev.next_trick_hint}`));
  }
}

// ---------- init ----------

document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("next-deal-btn").addEventListener("click", nextDeal);
  document.getElementById("claim-btn").addEventListener("click", claimRest);
  document.getElementById("undo-btn").addEventListener("click", undoLast);
  document.getElementById("replay-btn").addEventListener("click", replayDeal);
  const reviewBtn = document.getElementById("review-btn");
  // Pointer capture keeps pointerup firing on the button even if the cursor
  // drifts off mid-press, so the auction stays up while the user holds.
  reviewBtn.addEventListener("pointerdown", (ev) => {
    if (reviewBtn.disabled) return;
    reviewBtn.setPointerCapture(ev.pointerId);
    startReview();
  });
  reviewBtn.addEventListener("pointerup", endReview);
  reviewBtn.addEventListener("pointercancel", endReview);
  window.addEventListener("blur", endReview);
  document.getElementById("search-input").addEventListener("input", (ev) => {
    applyMenuFilter(ev.target.value);
  });
  document.getElementById("role-select").addEventListener("change", () => {
    if (currentScenario) nextDeal();
  });

  // Settings + wizard wiring
  document.getElementById("settings-btn").addEventListener("click", openSettings);
  document.getElementById("settings-close").addEventListener("click", closeSettings);
  document.getElementById("settings-key-setup").addEventListener("click", openWizard);
  document.getElementById("settings-key-remove").addEventListener("click", removeKey);
  document.getElementById("settings-mode").addEventListener("change", (ev) => {
    document.getElementById("settings-trigger-row").style.display =
      ev.target.value === "coaching" ? "none" : "";
  });
  for (const b of document.querySelectorAll(".wizard-cancel")) {
    b.addEventListener("click", closeWizard);
  }
  for (const b of document.querySelectorAll(".wizard-next")) {
    b.addEventListener("click", () => showWizardStep(parseInt(b.getAttribute("data-next"), 10)));
  }
  for (const b of document.querySelectorAll(".wizard-back")) {
    b.addEventListener("click", () => showWizardStep(parseInt(b.getAttribute("data-back"), 10)));
  }
  document.getElementById("wizard-test-btn").addEventListener("click", testAndSaveKey);
  for (const b of document.querySelectorAll(".wizard-finish")) {
    b.addEventListener("click", closeWizard);
  }

  // Inference + grading wiring
  document.getElementById("inference-submit").addEventListener("click", submitInference);
  document.getElementById("inference-skip").addEventListener("click", skipInference);
  document.getElementById("grade-now-btn").addEventListener("click", openInferenceManually);
  document.getElementById("inference-hint").addEventListener("click", toggleHint);
  document.getElementById("feedback-close").addEventListener("click", () => {
    document.getElementById("feedback-panel").hidden = true;
    syncSidebarVisibility();
  });

  await loadMenu();
});
