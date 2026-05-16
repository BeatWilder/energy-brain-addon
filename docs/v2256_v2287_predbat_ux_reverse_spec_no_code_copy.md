# V2256-V2287 Predbat UX reverse-spec voor Energy Brain

## 1. Purpose

Predbat wordt in deze sprint alleen gebruikt als benchmark en referentie. Het doel is niet om Predbat na te bouwen, maar om op UX-niveau te begrijpen welke planningsbeelden voor huishoudens nuttig zijn.

Energy Brain blijft een zelfstandig systeem. Deze reverse-spec beschrijft Energy Brain-eigen schermen, teksten en acceptatiecriteria. Er wordt geen Predbat-broncode gekopieerd en er wordt geen Predbat-runtime toegevoegd.

## 2. Clean-room boundary

Deze grens is verplicht voor dit en elk vervolgwerk:

- geen Predbat source code gekopieerd
- geen Predbat imports
- geen Predbat runtime dependency
- geen runtime GitHub/docs scraping
- geen Predbat assets, screenshots, CSS of HTML gekopieerd
- geen Home Assistant writes
- geen service calls
- geen dispatch
- geen controller changes
- geen wijzigingen aan Energy Brain controller, main, HA client of parent runtime

Predbat mag alleen handmatig worden bestudeerd via publieke documentatie en repository-informatie. De output moet Energy Brain-specifiek zijn en in eigen woorden geschreven blijven.

## 3. What Predbat teaches at UX level

Predbat laat op UX-niveau zien dat een EMS-cockpit pas nuttig wordt als de gebruiker vooruit kan kijken in plaats van alleen technische waarden te zien.

- Battery prediction over time: de verwachte batterijvulling door de dag heen moet het centrale verhaal zijn.
- Plan card / plan windows: de planning moet zichtbaar zijn als perioden met een doel, zoals laden, vasthouden of export overwegen.
- Charge / hold / export windows: vensters moeten normale labels krijgen, niet alleen technische codes.
- Cost comparison: een gebruiker wil weten of het plan beter of slechter lijkt dan een simpele basislijn.
- Actual vs predicted: vertrouwen groeit pas als zichtbaar wordt of voorspelling en werkelijkheid overeenkomen.
- Scenario thinking: minder zon of meer verbruik moet als begrijpelijke onzekerheid zichtbaar zijn.
- Read-only planning: een plan kan nuttig zijn zonder meteen apparaten aan te sturen.
- Debug/advanced details: technische details zijn nodig voor diagnose, maar horen niet bovenaan.
- Warnings/degraded states: ontbrekende of onbetrouwbare data moet prominent worden uitgelegd.
- Explainability: elke stap moet zeggen wat er gebeurt, waarom, en wat dit betekent voor het huis.

## 4. What Energy Brain should adapt

Energy Brain moet deze concepten vertalen naar een eigen, rustige cockpit in gewone taal.

- Kort gezegd: een korte zin die uitlegt wat Energy Brain denkt en dat er niets wordt aangestuurd.
- Nu in huis: batterijvulling, zon, verbruik en netbalans in huishoudtaal.
- Simpele daglijn: Nu, Straks, Vanavond en Morgen met een simpele verwachting.
- Plan in gewone taal: labels zoals Laden met zon, Vasthouden en Bijna vol, laden begrensd.
- Kostenvergelijking: Energy Brain verwachting, simpele basisstrategie en verschil, met onzekerheid als data ontbreekt.
- Scenario's: Normaal, Minder zon en Meer verbruik als display-only onzekerheidsbeelden.
- Voorspelling vs werkelijkheid: pas vertrouwen tonen als er genoeg meetdata is.
- Veiligheid: altijd zichtbaar maken dat het scherm alleen meekijkt.
- Technische details: reason codes, constraints en ruwe plannerdata achter een uitklapbare debuglaag.

## 5. What Energy Brain should reject

Energy Brain moet de volgende Predbat-achtige of EMS-achtige patronen expliciet afwijzen:

- Predbat monolithic runtime shape
- copying source code
- direct inverter/device control in cockpit
- planner service calls
- broad multi-inverter complexity die niet past bij Energy Brain
- unsafe write buttons
- unexplained raw reason-code-first UI
- runtime dependency op Predbat
- UI-acties die planner of controller direct bedienen

## 6. Tesla-style Energy Brain direction

De richting blijft een kalm donker dashboard met hoge informatiedichtheid en weinig ruis. De eerste laag moet begrijpelijk zijn voor een normaal huishouden:

- simple cards first
- technische grafiek secondary
- cockpit explains decisions before showing raw details
- batterijverwachting als hoofdbeeld
- kosten, scenario's en veiligheid als korte kaarten
- advanced/debug details hidden by default

De cockpit moet niet voelen als een ontwikkelaarstabel. Hij moet antwoord geven op: wat gebeurt er nu, wat verwacht Energy Brain straks, waarom, wat betekent dit voor mijn huis, en is dit veilig?

## 7. Proposed future implementation backlog

- V2288-V2319 Predbat-style Energy Brain plan card: bouw een Energy Brain-eigen plan card met daglijn, vensters en simpele huishoudlabels.
- V2320-V2351 actual-vs-predicted read-only comparison: toon voorspelling versus werkelijkheid zonder controlepad.
- V2352-V2383 scenario cards normal/minder zon/meer verbruik: maak scenario-kaarten op basis van bestaande plannerdata of duidelijke fallback.
- V2384-V2415 cost comparison confidence labels: toon wanneer kostenvergelijking betrouwbaar, onzeker of alleen schaduwdata is.
- V2416-V2447 technical graph as collapsible debug view: verplaats technische grafiekdetails achter een uitklapbare inspectielaag.
- V2448-V2479 live snapshot data quality panel: toon of zon, verbruik, prijs en batterijdata vers genoeg zijn.

## 8. Acceptance criteria

Elke toekomstige implementatie op basis van deze spec moet:

- read-only blijven tenzij apart goedgekeurd
- controller protected houden
- smoke tests halen
- geen forbidden runtime surfaces bevatten
- begrijpelijk zijn voor een leek
- technische details beschikbaar houden maar niet als eerste tonen
- Predbat alleen als benchmark/reference gebruiken
- geen runtime dependency, geen gekopieerde broncode en geen runtime scraping toevoegen
