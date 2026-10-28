# Simulace vytápění TČ a plynem — v3

## Modely Gawliczek a výkonové tabulky

Výběr obsahuje pět samostatných modelů R290 Power World 6, 8,9, 11,4, 14,8 a 18,2 kW, pro které jsou k dispozici certifikáty KEYMARK i výkonové tabulky do −25 °C. Dřívější scénáře s jinými modely nelze importovat bez změny modelu.

K nim jsou přidány Gree Versati V 8 a 10 kW; tabulky výkonu a příkonu byly převzaty z dodaného manuálu, PDF strany 13–14. Mezi platnými body se interpoluje; chybějící kombinace venkovní a vodní teploty nejsou extrapolovány a čerpadlo pro ně nemá výkon. Pro vodu pod 25 °C se používá nejbližší tabulková teplota 25 °C. Tabulky pro Gree jsou v `scripts/gree-curves-data.js`.

Simulace používá tabulky minimálního a maximálního výkonu a příkonu pro venkovní teploty −25 až +21 °C a teploty vody 35, 45 a 55 °C. Mezi body interpoluje teplo a příkon; pro vodu mimo tento rozsah používá nejbližší tabulkovou hodnotu, pod −25 °C kompresor vypíná. TUV je odhad z topné mapy. Křivky a jejich zdroje jsou v `scripts/manufacturer-curves.js`. Pro 11,4 kW je přiřazen certifikát třífázového PW040-DKZLRS-E, který odpovídá výkonové tabulce.

Ověření: `node scripts/test_manufacturer_curves.cjs`, `node scripts/test_catalog.cjs`, `node scripts/test_model_v3.cjs`.

Interaktivní simulace modelového rodinného domu na historických topných sezónách Open-Meteo ERA5 (říjen–duben, pro Ostravu 1960–2026). Grafy a ekonomické přehledy zobrazují vybrané desetileté okno (výchozích nejnovějších 10 sezón 2016–2026) a modelový rok.

## Spuštění a sestavení

Otevřete `index.html` v prohlížeči. Data počasí, model i aplikační JavaScript jsou vloženy v HTML; místní Tailwind a ikony zůstávají součástí projektu. Vyhledávání obcí, nové počasí a externí odkazy vyžadují internet.

```powershell
python scripts/build_full_interactive_app.py
node scripts/test_model_v3.cjs
```

Generátor zapisuje výstupní soubor `index.html` v tomto projektu.

- `scripts/build_full_interactive_app.py`: HTML/CSS, původní grafy a meteorologický vstup.
- `scripts/model-v3.js`: společný fyzikální model a ekonomika.
- `scripts/review-ui-v3.js`: komfort, citlivost, ekonomický přehled, scénáře A/B, export/import a sdílení.
- `scripts/test_model_v3.cjs`: regresní testy bez dalších npm závislostí.

Moduly se při sestavení vloží do výsledného HTML. Upravujte zdrojové moduly nebo šablonu, nikoli pouze vygenerovaný HTML soubor.

## Změny v3

- Oba režimy používají stejnou energetickou bilanci se dvěma teplotními uzly a krokem 10 minut. Zmizelo umělé zvýšení teploty místnosti bez dodané energie.
- Karty řízení skutečně simulují oba režimy a uvádějí stejnou vybranou sezónu jako hlavní karty. Souhrny jasně označují pětiletý průměr.
- Sepnutí jsou přechody vypnuto → zapnuto při časovém rozlišení modelu. Provozní hodina se již nevydává za jeden start.
- Komfort uvádí průměr, minimum, maximum, hodiny a stupňohodiny mimo pásmo; zobrazují se dodané teplo, patrona, změna uložené energie a chyba energetické bilance.
- TUV má přednost ve výkonové kapacitě; společná patrona je omezena na 3 kW. Případná nedodaná TUV je výslovně vykázána. Volba standardního/poledního ohřevu se respektuje.
- Noční klid a popis akumulace odpovídají vybranému dni. Interval 22–06 h obsahuje osm hodin, součet dvou úseků téhož kalendářního dne.
- Sezónní ekonomika poměrně krátí roční paušály a servis. Celoroční režim doplňuje odhad letní TUV a plné paušály; mimo říjen–duben nesimuluje vytápění.
- ETS 2 je vypnutý volitelný cenový scénář. Výsledek uvádí i úsporu bez něj. Lze zadat rozdíl elektrického paušálu, plynový paušál a zachování přípojky.
- Citlivost ukazuje devět kombinací cen ±30 %, hraniční cenu elektřiny a mírnou/prostřední/studenou sezónu.
- Scénáře A/B uchovávají parametry a souhrn výsledků. JSON obsahuje i vlastní archiv počasí; odkaz přenáší scénář s výchozím archivem. Uložení v prohlížeči může být omezeno jeho kapacitou.
- Posuvníky mají přesné číselné vstupy, detailní sekce se otevírají podle potřeby a stránka umožňuje přiblížení na mobilu.
- Nová verze cache service workeru; čištění omezené na cache této aplikace.

## Interpretace výsledků

Nejde o certifikovaný návrhový software ani validaci konkrétního výrobku. Optimalizace preferuje denní topení 10–16 h s cílem vyššího COP; mimo okno snižuje teplotní cíl a podle potřeby dotápí. Nepoužívá budoucí počasí. Nejde o matematicky zaručené maximum COP.

COP se odvozuje z dosavadního katalogu a modelových korekcí. Certifikáty a hlukové údaje nebyly při této úpravě znovu ověřeny; zdrojové odkazy a omezení jsou přímo v aplikaci. Radiátory předávají teplo do uzlu místnosti bez akumulace v podlaze. Model neřeší detailní hydrauliku, povrchovou teplotu krytiny, odběrové špičky TUV, investice ani budoucí vývoj cen.

Úspory se vždy počítají z aktuálního nastavení. Porovnávejte současně komfort a dodané teplo. Uložené starší režimy se při načtení převedou na denní optimalizaci a přepočítají.

## Ověření

Testy kontrolují syntaxi sestaveného JavaScriptu, všech deset sezón, zachování energie, součet denních spotřeb, nulový rozdíl při volbě reference, oddělený ETS 2, roční TUV, vypnutou i standardní TUV, nedostatečný výkon za mrazu a radiátorovou bilanci. V prohlížeči byly ověřeny přepínače ekonomiky, uložení/obnova A/B, shoda přehledu plynu a denní detail mrazu.

Nasazení na GitHub Pages je samostatný krok; místní sestavení nic nepublikuje.

Lokální úprava 25. 10. 2026: pouze Základ a Optimalizace · denní topení.

Zjednodušení rozhraní: odstraněna celá karta „Výsledek a jeho podmínky“ včetně vložených sekcí. Hlavní výsledky, volby dvou režimů, grafy a srovnání plynu zůstávají. Výpočtový model se tímto krokem nemění.

## Detailní ceníky energií (lokální úprava 25. 10. 2026)

Rozbalovací karta Nastavení energií používá ČEZ Fix na 3 roky, ČEZ Distribuci a GasNet. Výchozí D02d a jistič 3×25 A lze změnit; D57d je dostupná pro srovnání při splnění podmínek distributora. Zadané ceny obsahují DPH. Každá složka ceny i stálých plateb je upravitelná.

Volba „Elektro přípojku stejně používám“ vyřadí pouze jistič. Ostatní elektrické paušály mají samostatný přepínač. Průměr v záhlaví zahrnuje vybrané paušály při referenční roční spotřebě (výchozí elektřina 5 000 kWh, plyn 16 000 kWh). Simulace oceňuje skutečnou spotřebu variabilní cenou a paušály přičítá samostatně. D57d používá nastavitelný podíl spotřeby v NT, výchozích 83,33 % je odhad.

Zdroje: [elektřina od 30. 1. 2026](https://www.cez.cz/webpublic/file/edee/ceniky/moo_ele_cez_fix_na_3_roky_30012026_012026.pdf), [plyn od 17. 4. 2026](https://www.cez.cz/webpublic/file/edee/ceniky/moo_mop_plyn_gasnet_fix_na_3_roky_17042026_012026.pdf). Regulované ceny jsou od 1. 1. 2026. Výběr produktu porovnává standardní nabídky Fix 3 roky, Online 1 rok a Na neurčito; nezahrnuje individuální nabídky ani bonusy.

Implementace: `scripts/energy-prices.js`. Ověření: `node scripts/test_energy_prices.cjs` a `node scripts/test_model_v3.cjs`. Testy cen kontrolují skládání položek, vyloučení jističe, NT/VT, vlastní ceny, validaci a započtení paušálů právě jednou. V prohlížeči ověřeno rozbalení, přepínač jističe a změna D02d/D57d s přepočtem výsledků.

Další lokální úprava: cena ETS 2 přesunuta do rozbalovací karty energií, výchozích 30 €/t CO₂. Jediným volitelným řízením je denní optimalizace; ekviterm zůstává interní referencí úspor. Tolerance 0–3 °C vymezuje pásmo [cíl − tolerance, cíl], včetně grafu a kapacity akumulace. Cíl řízení nikdy nepřekračuje nastavenou teplotu; skutečná teplota může kvůli setrvačnosti či solárním ziskům pásmo překročit. Ověřeny krajní tolerance, bilance všech sezón a ceny.


Úprava rozhraní: odstraněna řada šesti souhrnných karet. Nastavení čerpadla je samostatně sbalitelné (výchozí sbalené); COP W35/W55, návrhové výkony a minimální modulace jsou editovatelné. Změny platí v aktuálním otevření stránky a nemění databázi; tlačítko obnoví model. SCOP a referenční údaje TUV zůstávají informativní. V nastavení domu je přichycený přehled aktuálních nákladů a rozdílů vůči referenci; referenci lze nastavit tlačítkem. Ostatní elektrické paušály jsou z výpočtu odstraněny i při načtení staršího nastavení. Jistič a paušály plynu zůstávají. Ověřeno v prohlížeči zvýšení ztráty 5,8 → 7 kW i snížení COP A7W35 5,3 → 4 a okamžitá změna nákladů.
