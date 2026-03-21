//Script,onDataLoad
window.setDealerCode = function (dealerCode, dealer = "S", rotateDeals = true) {
    window.pbsDealer = dealer;
    window.pbsRotateDeals = rotateDeals;
    if (window.updateRotateButton) window.updateRotateButton();

    var savedCompareEnabled = window.bbaCompareEnabled || false;
    var txtar = null;
    var doc = parent.window.document;
    var dirs = "SWNE";
    var step = 0;
    var stepStart = Date.now();
    var maxWait = 5000;

    var steps = [
        // step 0: close dialog if already open
        {
            ready: () => true,
            action: () => {
                var btn = $("modal-content button", doc)[0];
                if (btn) btn.dispatchEvent(new Event("click"));
            }
        },
        // step 1: open Deal Source dialog
        {
            ready: () => true,
            action: () => {
                var labels = [
                    'Deal source','Source de la donne','Fuente de la mano','Fonte da mãos',
                    'Quelle für Verteilungen','Origine della mano','Sursa donelor','Spelbron',
                    'Givkälla','Fordelingskilde','Hånd-kilde','Jakolähde','Źródło rozdań',
                    'Definice rozdání','Leosztások forrása','За раздаване','Bord kaynağı',
                    '源牌局','发牌机设置'
                ];
                labels.forEach(l => $("menu-item div:contains('" + l + "')", doc).trigger("click"));
            }
        },
        // step 2: wait for modal, then click Advanced tab
        {
            ready: () => $("modal-content", doc).length > 0,
            action: () => {
                var advLabels = [
                    'Advanced','Avancé','Avanzado','Avançado','D:Fortgeschritten','Avanzato',
                    'Avansat','Gevorderd','Avancerad','Viderekommen','Avansert','Edistynyt',
                    'Zaawansowany','Pokročilý','Haladó','Напреднал','İleri düzey','高級','高级'
                ];
                advLabels.forEach(l => $("modal-content div:contains('" + l + "')", doc).trigger("click"));
                if (dealerCode === "") { clearInterval(intrv); }
            }
        },
        // step 3: wait for Advanced tab to load, then select dealer
        {
            ready: () => $("modal-content mat-select", doc).length > 0,
            action: () => {
                $("modal-content mat-select", doc).click();
                $("mat-option", doc).each(function (idx) {
                    if ($("mat-pseudo-checkbox", this).hasClass("mat-pseudo-checkbox-checked")) {
                        if (dealer.includes(dirs.charAt(idx))) return;
                        this.click();
                    } else {
                        if (dealer.includes(dirs.charAt(idx))) this.click();
                    }
                });
            }
        },
        // step 4: wait for dealer dropdown to close, then check Randomly checkbox
        {
            ready: () => $("mat-option", doc).length === 0,
            action: () => {
                if (($("modal-content mat-checkbox:first", doc).hasClass("mat-checkbox-checked")) != rotateDeals) {
                    $("modal-content mat-checkbox:first .mat-checkbox-input", doc).trigger("click");
                }
            }
        },
        // step 5: check "Use this input" checkbox
        {
            ready: () => true,
            action: () => {
                if (!$("modal-content mat-checkbox:last", doc).hasClass("mat-checkbox-checked")) {
                    $("modal-content mat-checkbox:last .mat-checkbox-input", doc).trigger("click");
                }
            }
        },
        // step 6: get textarea and fill with dealer code
        {
            ready: () => true,
            action: () => {
                txtar = doc.querySelector("bidding-deal-source-popup textarea");
                if (txtar) {
                    txtar.focus();
                    txtar.value = dealerCode;
                    txtar.focus();
                }
            }
        },
        // step 7: dispatch input event so BBO registers the change
        {
            ready: () => !!txtar,
            action: () => {
                txtar.dispatchEvent(new Event('input'));
            }
        },
        // step 8: close dialog
        {
            ready: () => true,
            action: () => {
                $("modal-content button", doc)[0].dispatchEvent(new Event("click"));
                setTimeout(function () {
                    window.bbaCompareEnabled = savedCompareEnabled;
                }, 600);
            }
        },
        // step 9: wait for modal to close, then redeal
        {
            ready: () => $("modal-content", doc).length === 0,
            action: () => {
                $(".redeal-button", PWD).click();
            }
        }
    ];

    var intrv = setInterval(() => {
        try {
            if (step >= steps.length) { clearInterval(intrv); return; }
            if (Date.now() - stepStart > maxWait) { step++; stepStart = Date.now(); return; }
            if (!steps[step].ready()) return;
            steps[step].action();
            step++;
            stepStart = Date.now();
        } catch (e) {
            step++;
            stepStart = Date.now();
        }
    }, 50);
};
//Script