//Script,onDataLoad
window.toggleRandomlyRotate = function () {
    var delayValue = 500;
    var cnt = -1;
    var intrv;
    intrv = setInterval(() => {
        try {
            cnt++;
            switch (cnt) {
                case 0:
                    // Close dialog if already open
                    $("modal-content button", parent.window.document)[0].dispatchEvent(new Event("click"));
                    break;
                case 1:
                    // Open Deal source dialog
                    $("menu-item div:contains('Deal source')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Source de la donne')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Fuente de la mano')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Fonte da mãos')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Quelle für Verteilungen')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Origine della mano')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Sursa donelor')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Spelbron')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Givkälla')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Fordelingskilde')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Hånd-kilde')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Jakolähde')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Źródło rozdań')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Definice rozdání')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Leosztások forrása')", parent.window.document).trigger("click");
                    $("menu-item div:contains('За раздаване')", parent.window.document).trigger("click");
                    $("menu-item div:contains('Bord kaynağı')", parent.window.document).trigger("click");
                    $("menu-item div:contains('源牌局')", parent.window.document).trigger("click");
                    $("menu-item div:contains('发牌机设置')", parent.window.document).trigger("click");
                    break;
                case 2:
                    // Select "Advanced" tab
                    $("modal-content div:contains('Advanced')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avancé')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avanzado')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avançado')", parent.window.document).trigger("click");
                    $("modal-content div:contains('D:Fortgeschritten')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avanzato')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avansat')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Gevorderd')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avancerad')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Viderekommen')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Avansert')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Edistynyt')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Zaawansowany')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Pokročilý')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Haladó')", parent.window.document).trigger("click");
                    $("modal-content div:contains('Напреднал')", parent.window.document).trigger("click");
                    $("modal-content div:contains('İleri düzey')", parent.window.document).trigger("click");
                    $("modal-content div:contains('高級')", parent.window.document).trigger("click");
                    $("modal-content div:contains('高级')", parent.window.document).trigger("click");
                    break;
                case 3:
                    // Toggle "Randomly rotate" checkbox
                    $("modal-content mat-checkbox:first .mat-checkbox-input", parent.window.document).trigger("click");
                    break;
                case 4:
                    // Close dialog
                    $("modal-content button", parent.window.document)[0].dispatchEvent(new Event("click"));
                    clearInterval(intrv);
                    break;
                case 9:
                    // Prevent endless loop
                    clearInterval(intrv);
                    break;
            }
        } catch {
        }
    }, delayValue);
};
//Script
