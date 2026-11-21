# Climator – hybride verwarming voor Home Assistant

Stuurt een airco (warmtepomp) en een CV-thermostaat samen aan op de laagste kosten.
Leert zelf hoe snel en tegen welke kosten elke bron opwarmt, per buitentemperatuur,
en warmt vooraf op zodat het op de ingestelde tijd warm is.

## Installatie
1. HACS → ⋮ → *Custom repositories* → `https://github.com/tuei2/Climator`, type *Integration* → installeren.
   (Of handmatig: kopieer `custom_components/hybrid_heating` naar `/config/custom_components/`.)
2. Herstart Home Assistant.
3. Instellingen → Apparaten & diensten → Integratie toevoegen → **Climator**.

## Wat je kiest bij het instellen
| Veld | Voorbeeld |
|---|---|
| Ruimtetemperatuur (bron) | elke temperatuursensor in de kamer |
| Buitentemperatuur | je buitensensor |
| Airco | `climate.<faikin>` |
| CV-thermostaat | `climate.anna` |
| Energie airco (kWh, oplopend) | Faikin-energiesensor of een *Integraal*-helper op het vermogen |
| Gasmeter (m³, oplopend) | P1/DSMR gasmeterstand |
| Tapwater actief (optioneel) | Plugwise `binary_sensor …dhw_state` – sluit douchegas uit van het leren |

Prijzen, offsets enz. pas je later aan via **Configureren** op de integratie.

## Entiteiten
- `climate.<naam>` – **Uit** (module stuurt niets, maar leert wel mee), **Verwarmen** (vaste temperatuur), **Auto** (schema + voorverwarmen).
- `number` Comfort- en Ecotemperatuur, `time` Comfort vanaf / tot.
- `sensor` Strategie (airco / cv / beide), Fase, Start voorverwarmen, kosten per uur per bron, Leerdata (diagnostisch, met alle geleerde waarden per buitentemperatuur).
- Dienst `hybrid_heating.reset_learning` wist de leerdata.

## Hoe beslist hij
- **Opwarmen**: per bron (airco, CV, beide) wordt duur en kosten berekend uit de geleerde
  °C/uur en kWh of m³ per °C. De goedkoopste optie die op tijd klaar is wint; lukt dat niet, dan de snelste.
- **Op temperatuur houden**: de bron met de laagste kosten per uur
  (verbruik per uur per graad verschil tussen binnen en buiten × prijs).
- **Voorverwarmen** (Auto): starttijd = comfort-start − verwachte opwarmtijd − marge.
- De niet-actieve airco gaat **uit**, de niet-actieve CV gaat naar de *setback*-temperatuur (standaard 15 °C).
- Airco krijgt doel + offset (standaard +1 °C, omdat de unit op eigen hoogte meet).

## Alleen leren
Zet de module op **Uit**. Hij stuurt dan niets aan, maar kijkt wat de airco en Anna doen
(aan/uit, setpoint) en leert daarvan. Zo kun je eerst een week gewoon stoken zoals je gewend bent
en daarna pas *Auto* aanzetten met al geleerde waarden.

## Afstandsbediening / Anna-knop / app
Verander je zelf iets aan de airco of Anna terwijl de module stuurt, dan ziet hij dat
(na 2 minuten) en **pauzeert** hij (standaard 120 minuten, instelbaar via *Configureren*;
0 = de module zet het terug). Tijdens de pauze leert hij mee. Daarna, of zodra je in de module
zelf de temperatuur of modus wijzigt, neemt hij het weer over. De `climate`-entiteit toont
`override_until`.

## Goed om te weten
- **Plugwise Anna**: de module zet de Anna op *heat* (handmatig). Daarmee staat het Anna-schema uit;
  het schema loopt via deze module. Zet de module op *Uit* en de Anna terug op *auto* om terug te gaan.
- **Leren** gebeurt in meetvensters (opwarmen 15–45 min, onderhouden 60 min). Na een paar
  dagen per buitentemperatuur-band worden de keuzes nauwkeurig; tot die tijd gebruikt hij redelijke standaardwaarden.
- **DSMR4-meters** geven het gas maar eens per uur door; opwarmmetingen met gas zijn dan grof.
  DSMR5 (elke 5 minuten) werkt prima.
- Alles draait lokaal; logboek: `custom_components.hybrid_heating`.

## Nieuwe versie uitbrengen
Verhoog `version` in `custom_components/hybrid_heating/manifest.json` en push naar `main`.
De workflow maakt automatisch een release `vX.Y.Z`; HACS toont daarna een update.
