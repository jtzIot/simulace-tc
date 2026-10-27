# Lokální konfigurace v záložkách (26. 10. 2026)

Změny nejsou publikované na GitHub. Zdroj: scripts/workspace-ui.js, tariff-control.js, model-v3.js a energy-prices.js. HTML regeneruje scripts/refresh_preview.py se zachováním uloženého počasí, případně původní builder.

Šest záložek: lokace, dům, TČ, referenční plynový kotel, tarify ČEZ, řízení. Při nastavování zůstávají viditelné ceny obou zdrojů, úspora, rozdíl proti uloženému srovnání a komfort. Detail výpočtu ukazuje náklady po složkách. Kotel má oddělenou účinnost vytápění a TUV vůči Hs. Model kotle vychází ze stejného dodaného tepla; nepočítá jeho hodinovou dynamiku, cyklování ani výkonové omezení.

ČEZ D01d, D02d, D25d, D26d, D57d. D75d není uvedena v aktuálním přehledu sazeb. Výchozí zůstává D02d. Ceníky včetně DPH zůstávají editovatelné. Sazba mění ceny a vzorový denní rozvrh NT; reálné HDO odběrného místa není stahováno. Rozvrh lze upravit s kontrolou délky a intervalů. Model běží po 10 minutách a náklady sčítá podle skutečné spotřeby ve VT a NT, nikoli podle odhadnutého podílu spotřeby.

D25d/D26d: 8 h NT, zásobník TUV se ohřívá v NT. Samotné TČ nezakládá nárok na akumulační sazbu. D57d: 20 h NT, patrona je blokovaná ve VT; kompresor je podle podmínek sazby z povinného blokování vyňat. Volitelné blokování kompresoru představuje vlastní zapojení. TUV je rozložena do 12 desetiminutových kroků denně v dostupných pásmech; při chybějícím výkonu se vykazuje nedodaná energie. Není simulován stav zásobníku ani odběr vody v jednotlivých hodinách. Letní TUV zůstává zjednodušeným odhadem s pevným COP.

Řízení: denní priorita, priorita NT, stálá teplota. Nastavit lze denní okno a využití tolerance směrem dolů. Optimalizace je pravidlová, nikoli matematicky zaručené optimum COP nebo ceny. Komfort může být překročen kvůli setrvačnosti nebo nedostatečnému výkonu; přehled na to upozorňuje.

Zdroje: https://www.cez.cz/webpublic/file/edee/ceniky/moo_ele_cez_fix_na_3_roky_30012026_012026.pdf a https://www.cezdistribuce.cz/file/edee/distribuce/ceniky/ceniky-a-podminky/podminky_distribucnich_sazeb_domacnost.pdf

Ověření: test_model_v3.cjs, test_energy_prices.cjs, test_audit.cjs, test_tariff_control.cjs. Nové testy kontrolují všechny sazby, energetickou bilanci, fakturaci VT/NT, rozvrh TUV, validaci HDO, blokování a oddělenou účinnost TUV kotle. Prohlížeč: všechny záložky, změna tepelné ztráty, tarif D25d, široké a úzké rozhraní.


## Úpravy 27. 10. 2026

Spodní katalog TČ byl odstraněn z navigace i hromadného rozbalení. Databáze čerpadel zůstává pro konfiguraci TČ. Tarify ČEZ se jmenují Tarify energie. V režimech řízení je synchronizovaná sazba a ovládání cílové teploty a tolerance vychladnutí. Denní priorita vysvětluje využití akumulace a vyššího COP v teplejší části dne.

Graf venkovní teploty je oddělen od vnitřních teplot. Všechny tři denní grafy zobrazují desetiminutový rozvrh NT/VT a přechody HDO. Jde o modelový denní rozvrh, ne živé HDO. Teploty v tooltipu jsou formátované na dvě desetinná místa. Denní/noční téma si prohlížeč pamatuje. Rozbalovací vysvětlení uvádí význam uloženého cenového srovnání i uložené částky.

Výchozí označení kotle je Protherm Gepard Condens 25 MKO-A. Technické údaje: https://protherm.cz/files/downloads/projekcni-podklady/pp-1-6-gepard-condens-verze-2-09032023-2605641.pdf . Účinnosti výpočtu zůstávají editovatelné sezónní předpoklady Hs; nepřebírají katalogové hodnoty Hi. Databáze EPREL je dostupná odkazem pro ruční vyhledání a přepis hodnot. Automatické API není připojené, vyžaduje vydaný klíč: https://eprel.ec.europa.eu/screen/requestpublicapikey .

Ověření: všechny čtyři existující testovací sady; headless Chrome – sestavení workspace, odstraněný katalog, synchronizace sazby D25d, řízení stálé teploty, přesunuté ovladače komfortu, světlé panely, výchozí kotel a vykreslení všech tří denních grafů.


## Verze 2026.10.27.2

Výchozí sazba D25d včetně jejích cen a jističe, referenční sazba domácnosti s plynem D02d. Výchozí označení kotle Gepard Condens 12 MKO; jeho sezónní účinnosti zůstávají editovatelnými předpoklady Hs. Šest kroků konfigurace je očíslováno. Popisek „Pásmo tolerované teploty (nekomfort)“ označuje povolený pokles pod cílovou teplotu.

Volitelná ostatní spotřeba domácnosti: roční součet a VT/NT, editovatelný seznam zahrnutých spotřebičů. Změna ročního součtu zachovává podíl VT/NT, změny dílčích kWh mění součet. Jednotarif účtuje vše ve VT. Domácnost s plynem má stejnou celkovou spotřebu a referenční jednotarif D01d/D02d; jeho cena se skládá z ceníku stejného dodavatele a společných regulovaných složek. Náklady a úspora spotřebičů jsou oddělené od vytápění; poměrná sezónní spotřeba je odhad, protože hodinový profil domácnosti není zadán. Rozdíl jističe zůstává pouze jednou ve vytápění. Jednotlivým spotřebičům se bez jejich dílčí spotřeby nevymýšlí vlastní úspora. Vlastní seznam je při vykreslení escapovaný. Export/import přes energy.household; starší scénáře dostanou vypnutou volbu.

Pravý panel je užší a nákladové karty jsou pod sebou. Uvádí starty kompresoru za vybranou sezónu včetně TUV, průměr přes vybrané sezóny a omezení desetiminutového rozlišení (bez letních startů). Souhrnné náklady zůstávají průměrem vybraných sezón. Formátování fyzikálních veličin má maximálně dvě desetinná místa, samotná bilance a fakturace stále používají plnou přesnost.

Nastavení domu má průvodce zadáním, aktuální návrhový mráz u tepelné ztráty, rozlišení skutečné soustavy a katalogového profilu W35/W55, srozumitelný cíl teploty vody při návrhovém mrazu a vysvětlení, že jde o bod topné křivky, nikoli celoroční konstantu. Plocha je plocha vytápěných místností a tloušťka se vztahuje k akumulačnímu potěru.

Ověření: test_model_v3.cjs, test_energy_prices.cjs, test_audit.cjs, test_tariff_control.cjs, test_household.cjs. Nový test obsahuje nezávislé faktury VT/NT a reference, sezónní odhad, vypnutou a nulovou spotřebu, stejné sazby, možné zdražení, vyloučení opakovaného jističe, validaci a kompatibilitu starších scénářů. Prohlížeč: výchozí sazba i kotel, synchronizace součtu/VT/NT, spotřebiče, starty, témata a svislé rozložení.


## Verze 2026.10.27.3

V Tarifech energie je volba „Rozpočítej dle typického profilu spotřebiče“. Roční kWh jednotlivých spotřebičů jsou upravitelné; lze přidávat/odebírat řádky a vybírat typ profilu. Profily jsou výslovně orientační předpoklady: lednice/mrazák a trvalý odběr rovnoměrně celý den, pračka 09–11 h, myčka 20–22 h, vaření v uvedených denních špičkách, osvětlení ráno/večer, elektronika hlavně večer. Nejde o naměřená data ani automatický přesun do NT. Jednotlivé profily se opakují každý den bez víkendových/sezónních změn.

Podíl NT vzniká integrací vah profilu přes skutečný modelový rozvrh HDO v krocích 10 minut. Změna sazby i vlastních intervalů HDO okamžitě mění podíl. Rovnoměrný odběr má při 8 h NT podíl 1/3, při 20 h NT podíl 5/6. Změna celkových ročních kWh zachová poměr spotřebičů, přepnutí zpět do ručního režimu zachová vypočtené VT/NT. Editor zobrazuje pro každý spotřebič procento NT a roční kWh VT/NT. Export/import používá energy.household.mode a profiles; starší scénáře zachovávají ruční rozdělení.

Pět původních souhrnných karet je ve svislém sloupci vedle Průběžného výpočtu. Sloupec obsahuje výběr sezóny a vysvětluje rozdíl jedné sezóny proti průměrným nákladům. Na užší obrazovce se sloupce skládají pod sebe.

Spodní část používá přepínače Den – teploty a HDO, Sezóna – spotřeba, Porovnání 5 sezón, Tabulky, TČ a plyn, Vše pod sebou. Denní teploty a venkovní graf jsou vedle sebe, výkon a COP pod nimi. Měsíční tabulka je v přehledu tabulek. Kliknutí na den v sezónním grafu otevře denní pohled. Původní nápověda akumulace je rozbalovací.

Ověření: všech pět regresních sad včetně rozšířeného test_household.cjs. Nové kontroly ověřují 8/24 a 20/24 podíly NT, vlastní desetiminutové překryvy HDO, zachování celkových kWh, více profilů, jednotarif a validaci. Headless Chrome ověřil profilový editor, přepočet změnou sazby, zachování součtu, ruční režim, přesunuté karty, přepínače grafů, skutečnou viditelnost a rozměry denního canvasu, témata a úzkou obrazovku. Denní grafy byly také vizuálně zkontrolovány.


## Verze 2026.10.27.4 – Keymark 011-1W1325 a celkové náklady domu

Nový výchozí model je Warmhouse HM-M0-A1 z ověřeného certifikátu 011-1W1325, který odpovídá požadovanému bodu +12 °C / 2,35 kW / COP 8,95 (LT). Původní HM-M0-A2 a jeho přiřazení k 011-1W1163 nebyly ověřené; původní katalogové položky zůstávají označené jako odhady. Zdroj: https://www.heatpumpkeymark.com/en/?cHash=e30201a2dfb606558afd1b027939d014&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=7863&type=109126 . Datový a výpočetní modul: scripts/hp-keymark.js.

Konfigurace obsahuje Pdh, COP a Cdh pro -10 (TOL), -7 (Tbiv), +2, +7, +12 °C pro LT i MT; příkon Pdh/COP je dopočtený. Samostatně EN14511 A7/W35 a A7/W55 výkon/příkon/COP, Prated, Tbiv, TOL, WTOL, Poff/PTO/PSB/PCK, PSUP, SCOP, ηs a QHE. U každého je popsané použití. Náplň chladiva 0,57 kg a LWA 56 dB(A) jsou informativní. Hodnoty jsou editovatelné; originál databáze se nemění. Export/import přenáší i upravené měření a minimální modulaci. Byla opravena validace importu výchozího anonymního počasí se souřadnicemi null.

Částečné EN14825 body nelze zaměnit za pevnou vodu 35/55 °C ani za maximální/minimální výkon. Voda LT 35/34/30/27/24 °C a MT 55/52/42/36/30 °C je výslovně označený upravitelný předpoklad proměnné vody, ne údaj doložený veřejným záznamem tohoto výrobku. Obecný příklad zkušebních podmínek: https://heatpumpsireland.ie/wpcms/wp-content/uploads/2018/06/4P01457-01-rev-1-Report-9AQ.pdf . Pro tento výrobek je potřebný úplný laboratorní protokol pro potvrzení těchto podmínek.

Interpolace venkovních bodů používá tepelný a elektrický výkon, vodní interpolace používá COP. Mimo vodní rozsah je omezená modelová korekce 2 %/K; nad +12 °C se venkovní hodnota drží. Odhad plného zatížení je ukotvený v samostatné zkoušce A7W35/W55. Kapacitní obálka je pouze odhad mezi deklarací při TOL a jmenovitým výkonem při +7 °C; teplý Pdh není maximem. Pod TOL nebo nad WTOL kompresor neběží; kapacita pro TUV se vyhodnocuje při její teplotě. Nejde o certifikovanou plnou výkonovou mapu. Minimální modulace 2,5 kW a externí oběhové čerpadlo 25 W jsou upravitelné předpoklady, nikoli výsledky z veřejného certifikátu.

Cdh je dostupný pro volitelnou dodatečnou degradaci pod zkušebním Pdh (výchozí vypnuto kvůli riziku opakované korekce). Další původní vlhkostní srážka za odmrazování se u nové sady nepřidává. Zapnuté PSB/Poff vstupují do zimní elektrické bilance; blokovaný kompresor tedy může stále odebírat 10 W. PTO a PCK zůstávají informativní, protože jejich režimy nejsou samostatně modelované. Tbiv ani PSUP nepřepisují instalovaný dům/patronu; SCOP/ηs/QHE nevynucují výsledek simulace. TUV z topných dat je odhad, není doložený test EN16147. Letní paušální odhad nezahrnuje klidové příkony.

Patrona dodává nedostatek výkonu s limitem 3 kW společným pro vytápění a TUV; TUV má přednost a vytápění vyžaduje pokles pod toleranci. Tepelná a elektrická energie patrony jsou stejné (COP 1), energie vzniká integrací výkonu po 10 minutách. Nejde o pevné procento výkonu kompresoru. Při D57d se respektuje blokování ve VT. Výsledná minima pokojové teploty mohou být nižší: nový model skutečně vypíná pod deklarovaným TOL -10 °C a nemá dřívější neověřený výkon.

Horní karta Průběžného výpočtu zvýrazňuje součet vytápění/TUV + zadaných ostatních spotřebičů pro variantu TČ i plynu, včetně v modelu již započtených paušálů a servisu. Zbytek domu se nepřičítá dvakrát. Bez zapnuté ostatní spotřeby karta výslovně říká, že jde pouze o vytápění a TUV. Období a rozsah jsou uvedené přímo u částek. Samostatné náklady vytápění a TUV jsou rozbalovací.

Ověření: nová sada test_keymark.cjs pro přesné body, plné/částečné zatížení, kapacitu, TOL/WTOL, interpolaci, pomocné příkony, Cdh, validaci a sdílenou patronu. Rozšířený test_tariff_control.cjs při blokování kontroluje nulové teplo kompresoru a správný Poff, nikoli nesprávně nulovou celkovou elektřinu. Zachovány všechny předchozí sady. Chrome: 10 řádků LT/MT, +12 °C bod, změna a obnova, originál bez mutace, export/import a součet hlavní ceny domu.


## Verze 2026.10.27.5 – celý katalog, 2 MWh domácnost a teoretické řízení

Všech devět položek hlavního výběru má podrobné ověřené tabulky pro konkrétní sestavu a průměrné klima. K dosavadnímu HM-M0-A1 (011-1W1325) přibyly HM-M1-A1 (011-1W1163), HM-M2-A1 (011-1W1160), Vitocal 250-A AWO-M-E-AC 251.A08 (011-1W0590), NIBE S2125-8 1x230V (012-C700114 / Issue 3), Vaillant VWL 75/6 A 230V (011-1W0760), Panasonic WH-SDC0509L3E5 / WH-WDG07LE5 (011-1W0631), Bosch CS5800iAW 7 OR180 MCP-S (011-1W0675), Daikin ERRA08EV3 / ELVH12S23E(6V/9W) (011-1W0652). Nesprávná stará označení/certifikáty byly opravené. Neidentifikované HM-M0-A2 není nabízené jako ověřený model; jeho staré id zůstává jen kvůli importu starších scénářů.

Datové podklady jsou v sim_data/keymark/*.json včetně původních modelů, skupin zkoušek a zdrojových URL. scripts/fetch_keymark_sources.py bez --refresh použije uložené JSON, --refresh načte zdroje znovu. scripts/build_keymark_catalog.py z nich vybírá přesné modely a průměrné klima do scripts/keymark-catalog-data.js. Dlouhý report Viessmann vyžadoval delší síťový limit; nakonec byl získán celý, nikoli nahrazen jiným modelem. Všechny nové moduly se vkládají do výsledného index.html, který zůstává použitelný offline.

Schéma zvládá rozdílný počet bodů v LT/MT včetně samostatného Tbiv a prázdného Cdh. Chybějící Cdh se zobrazuje prázdně a při výpočtu nevytváří dodatečnou korekci. EN16147 konkrétní sestavy je zobrazený tam, kde existuje; nesměšuje se s úplným modelem jiného zásobníku. Typické teploty proměnné vody, minimální modulace, kapacitní obálka a chování mimo měřené body zůstávají označenými předpoklady. Horní kapacita se odhaduje z nejvyššího doloženého výkonu, nikoli z nejmenšího Pdh nebo referenčního Prated budovy. Jde stále o aproximaci, ne o úplnou maximální výkonovou mapu. Podmíněný normový bod TOL/Tdesignh je při průměrném klimatu přiřazen max(TOL,-10 °C).

Spotřeba ostatních spotřebičů je nově výchozí zapnutá na 2 000 kWh/rok se zapnutými typickými profily. Předvyplněný mix je jen odhad, lze měnit spotřebiče a kWh. Starší import bez těchto údajů zachovává vypnutou volbu a ruční interpretaci, aby mu změna výchozích hodnot sama neměnila účet. Krok 5 se jmenuje „Tarify energie a spotřeba domácnosti“. V Průběžném výpočtu je trvale vidět samostatná spotřeba elektřiny vytápění + TUV včetně VT/NT, bez ostatních spotřebičů. Je označená jako průměr vybraných sezón; TUV v ročním režimu zahrnuje i letní odhad.

Nová volba „Teoretické optimum · cena tepla“ je konečné zpětné srovnání pěti skutečně simulovaných strategií: reference se stálým cílem, denní priorita, priorita NT, stálá teplota s nastaveným režimem TUV a ekonomická priorita. Ekonomická varianta využívá ideální znalost historického počasí dne a řadí 10minutové sloty podle ceny elektřiny / COP při odhadnuté aktuální teplotě vody a zatížení. Počet slotů odvozuje z odhadnuté denní potřeby tepla a dostupné kapacity. Vlastní fyzikální simulace teprve určí reálný provoz, komfort a cenu. HDO blokování, TOL/WTOL, společná patrona a TUV se respektují. Dražší VT může být levnější na dodané teplo díky vyššímu COP; test obsahuje takový konkrétní syntetický den.

Vybere se nejnižší skutečně spočtená cena z kandidátů při omezeních vůči referenci: minimum/maximální teplota (0,05 K tolerance porovnání), hodiny i stupňohodiny mimo pásmo, nedodaná TUV, alespoň 99,5 % referenčního dodaného tepla a koncová uložená energie nejvýše o 0,1 kWh nižší. Referenční varianta je zahrnutá, takže výsledek může být reference s nulovou úsporou. Nejde o prokázané globální minimum a rozhraní to výslovně říká. I reference může mít při nedostatku výkonu horší komfort. Režim nepředstírá reálnou předpověď a neoptimalizuje podrobný stav zásobníku TUV. Zobrazuje vybranou strategii, ceny a přijatelnost všech kandidátů i orientační nejlevnější hodinu zvoleného dne. Export/import zachovává řízení; starší scénáře bez řízení přejdou na denní prioritu.

Ověření: sedm testovacích sad včetně nového test_theoretical.cjs pro všechny modelové identity, měřené uzly, 2 MWh výchozí profily, teplý VT proti studenému NT, výběr z pěti variant, komfort a koncovou energii, bilanci i blokování HDO. Prohlížeč: všechny modely a jejich zdrojové odkazy, odpovídající počet řádků LT/MT, výchozí domácnost, nový název, samostatná elektřina vytápění/TUV, teoretický režim a jeho export/import. Standardní headless export Chrome se při testu zasekl; přímé ověření přes diagnostické rozhraní téhož skrytého testovacího prohlížeče prošlo.


## Verze 2026.10.27.6 – odstranění Teoretického optima

Na požadavek kvůli rychlosti je experimentální režim kompletně odstraněný z nabídky, modelu, sestavování i zdrojových souborů. Zmizelo hledání pěti variant, ekonomický plán dne i ukládání desetiminutových priorit do každé hodiny. Výpočet znovu simuluje pouze referenční a zvolený režim. Zůstávají denní priorita, priorita NT a stálá teplota. Import starých scénářů s policy optimum/economic přejde na day; stejná migrace chrání i přímý přepočet starého stavu.

Údaje Keymark, 2 MWh domácnosti s profily, samostatná elektřina vytápění/TUV a celkové náklady domu zůstávají. Test katalogu a migrace je nyní scripts/test_catalog.cjs; původní experimentální test i modul byly odstraněné.


## Verze 2026.10.27.7 – zpřehlednění GUI a oddělení ekonomického přepočtu

- Zrušeno třísloupcové rozložení se třemi vnořenými posuvníky. Konfigurace vlevo a Průběžný výpočet vpravo tvoří dvousloupcový layout bez vnořeného skrolování. Pět KPI karet vybrané sezóny je umístěno vodorovně přímo nad přepínači grafů společně s výběrem aktivní sezóny.
- Všechny posuvníky a jejich číselné vstupy (`.review-number`) jsou sloučené do jednoho řádku (`.slider-input-row`).
- Záložka 3 (Konfigurace TČ) zobrazuje nahoře souhrnnou čtveřici dlaždic (výkon A7, normový SCOP, chladivo/hlučnost, limity TOL/WTOL), instalační předpoklady a pravidelný servis TČ; detailní tabulky EN 14825 (LT/MT) a EN 14511 jsou zabalené v rozbalovacích sekcích `<details>`.
- V záložkách 4, 5 a 6 jsou formuláře rozdělené do přehledných dvousloupcových podkaret (`.config-subcard`) a haléřové složky ceníků elektřiny a plynu jsou zabalené pod rozbalovací detaily.
- Panel Průběžného výpočtu má sjednocenou hlavní kartu porovnání (S TČ vs. S plynovým kotlem + celková úspora a její rozpad), mřížku 2×2 klíčových ukazatelů (elektřina TČ, SCOP, komfort, starty kompresoru) a rozbalovací lištu pro porovnání změn, uložení/načtení scénářů A/B a export/import JSON (včetně názvu kotle a účinnosti TUV).
- Oddělen rychlý přepočet ekonomiky (`recalculateEconomy`) od fyzikální simulace (`recalculateSimulation`): změny ceníků, ETS 2, servisu či účinnosti kotle přepočítají výsledky okamžitě bez opakovaného spouštění 10minutové fyzikální bilance.


## Verze 2026.10.27.8 – Ostrava (1960–2026), 10 sezón, Modelový rok a rozšíření katalogu R290

- Výchozí modelová lokalita je nastavena na Ostravu (211 m n. m., výpočtová teplota -12 °C) s referenčním hodinovým archivem Open-Meteo ERA5 pro všech 66 otopných sezón 1960–2026 (`1960-10-01` až `2026-04-30`).
- Období simulace používá 10leté okno okolo zadaného roku (1960–2026); výchozím obdobím je nejnovějších 10 sezón (`2016-2017` až `2025-2026`).
- Výchozím nastavením v panelu Průběžný výpočet je `Modelový rok` (`economyPeriod: 'annual'`) se samostatným přepínačem zahrnutí či oddělení ostatních spotřebičů domácnosti.
- Katalog tepelných čerpadel je rozšířen o kompletní řadu Gawliczek R290 (Power World CleanLife 6 kW, 8,9 kW, 11,4 kW, 14,8 kW, 18,2 kW a Warmhouse R290 Ultra tiché 8,1 kW, 10 kW, 12 kW, 16,2 kW) s ověřenými certifikáty HP KEYMARK (celkem 15 ověřených modelů v katalogu).
- Ze skriptů, testů i dokumentace byly odstraněny všechny zbývající osobní identifikátory a lokální cesty při zachování všech veřejně přístupných ceníků, certifikátů a technických údajů.


## Verze 2026.10.27.9 – Zjednodušený režim a sbalitelné grafy

- Přidán přepínač v záhlaví mezi **⚡ Zjednodušeným režimem** (výchozí při načtení) a **🔧 Podrobným režimem** (všech 6 záložek konfigurace).
- Ve zjednodušeném režimu se vlevo zobrazují jen tři přehledné bloky nejdůležitějších parametrů (1. Lokalita a období simulace, 2. Dům, otopná soustava a ohřev TUV, 3. Zdroj tepla – výběr TČ, účinnost plynového kotle a povolenka EU ETS 2) bez duplikace ID ovládacích prvků.
- Vpravo v panelu **Průběžný výpočet** se ve zjednodušeném režimu zobrazuje pouze hlavní přehledová karta nákladů (TČ vs. plynový kotel, přepínač Modelový rok / Topná sezóna a přepínač Jen vytápění a TUV / Celý dům). Detailní dlaždice, vzorce a správa scénářů A/B se zobrazí v podrobném režimu.
- Spodní sekce **GRAFY A PODROBNÉ VÝSLEDKY** je v obou režimech ve výchozím stavu sbalená a lze ji kdykoli rozbalit/sbalit kliknutím na záhlaví nebo tlačítko `▼ Rozbalit grafy a podrobné výsledky`.
