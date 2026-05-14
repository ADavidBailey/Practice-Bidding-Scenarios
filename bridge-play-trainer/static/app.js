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
  if (state.role === "declarer") return state.declarer;
  if (state.role === "defender_e") return "E";
  if (state.role === "defender_w") return "W";
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
    document.getElementById("result-panel").hidden = true;
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

function startPlay() {
  awaitingPlay = false;
  auctionVisibleCount = null;
  if (lastState) render(lastState);
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
  await loadMenu();
});
