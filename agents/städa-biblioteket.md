# Städa Biblioteket

Diskussionen om Biblioteket och Miljön, sparad inför nästa session: läget, det som är beslutat, planen och de frågor
som är öppna. Inget av planen är påbörjat.

## Läget

- En tråd av typen `model` är ett alias (glossaryns :Handle): namnet är aliaset och huvudet vikterna (repo, revision,
  filer). Biblioteket visar den som "modell", och tråden visar bara filerna, så namnet och innehållet ger blandade bud.
- Bibliotekets sökruta visas så fort en lista inte är tom (`src/chatddx/portal/threads.py:library_page`, `of`), och
  någon paginering finns inte: hela listan visas alltid.
- Typer som inte skrivs i portalen visar längst ner "These are written through data sets, by developers and ops."
  (`src/chatddx/portal/templates/library.html`).
- Bibliotekets meny är `sticky` utan maxhöjd: en meny högre än fönstret rullar först när sidan nått botten.
- Miljön (`src/chatddx/portal/templates/world.html`) har sektionerna Världen, Källor, Ändpunkter, Värdar, Bindningar och
  Modeller; Modeller visar aliasets namn och dess fakta som JSON, Ändpunkter vilken inferensserver varje ändpunkt
  tillhandahåller.
- Hyllornas beskrivningar räknar upp innehållet, som "The models, the engines serving them and what is known about
  them.", i stället för att säga varför hyllan finns.

## Beslutat

- Från Biblioteket till Miljön: Modeller blir Alias, och Inferensservrar och Fakta flyttar med.
- Bibliotekets hylla Drift (engelska Operations) läggs sist och håller verktyg, facitschema och kanarieuppsättning.
- Ingen hylla för alias i Biblioteket: aliasen ligger i Miljön.
- Notisen längst ner tas bort, före den större städningen.
- Ordningen: flytten, sedan en ordentlig städning (reduce), sedan
  1. Bibliotekets meny rullar för sig, så att en lång sida inte måste rullas till botten först.
  2. Sökrutan villkoras.
  3. Global paginering och sök från 10 rader.
  4. Beskrivningarna skrivs om.

## Plan

### Fas 1, flytten

1. Ta bort notisen längst ner på typsidorna.
2. Biblioteket (`src/chatddx/portal/shelves.py`): modell, inferensserver och fakta tas bort; hyllan Drift sist med
   verktyg (från Konfigurationer), facitschema (från Fall) och kanarieuppsättning. Kontrollen vid start, att varje typ
   ligger på en hylla, blir att varje typ ligger på en hylla eller i Miljön.
3. Miljön: sektionen Alias ersätter Modeller, och sektionerna Inferensservrar och Fakta läggs till; varje post länkar
   till sin tråd, där dess historik finns kvar. Typen `model` behålls internt, i URL:er, API och kod; bara var den visas
   ändras.
4. Texter, katalog, tester och dokumentation; hela `./check.sh`.

### Fas 2, städning (reduce)

Ta bort det som bara fanns för de flyttade typerna i Biblioteket, Miljöns gamla sektion Modeller, texter som inte
längre används och tester av borttagna vägar; slå ihop dubbletter som dyker upp.

### Fas 3

- (1) Menyn får en maxhöjd och egen rullning.
- (2, 3) En gemensam mekanism för sök och paginering från 10 rader; sökrutan (2) blir en del av den (3).
- (4) Nya beskrivningar som säger varför något finns.

## Öppet

1. Miljöns nya sektioner:
   - Alias: namn, vikter (repo@revision), inferensserver, ändpunkt och värd. Räcker det?
   - Inferensservrar överlappar Ändpunkter. Förslaget: ett kort per inferensserver, med vad den är låst till
     (hårdvara, programversion, vikter, chattmall, argument) och vilken ändpunkt som når den, medan Ändpunkter behåller
     adress, kapacitet, hemlighet och godkännanden. Eller slås de ihop?
   - Fakta: en läsbar tabell (resonemangsnivåer, rekommenderad sampling, gränser) i stället för JSON?
2. Gamla länkar som `/library?kind=model`: omdirigeras till rätt sektion i Miljön, eller 404?
3. Städningens omfattning: det flytten gör överflödigt, eller en bredare genomgång av portalen?
4. Global paginering:
   - Vilka listor: Bibliotekets (trådar och fall), Körningar, en tråds versioner och körningar, Rättningens tabeller,
     Miljöns sektioner, Uppdaterat; och öarnas listor, som Variations körningar?
   - Hur många rader per sida, och gränsen fler än 10 (från 11) eller från 10?
   - Ett gemensamt skript i webbläsaren, som lägger till sök och sidor på varje markerad lista (en implementation, men
     alla rader skickas), eller paginering på servern med `?page=` och `?q=` (klarar stora listor och fungerar utan
     JavaScript, men kräver arbete per sida)? Förslaget: skriptet, och servern bara där listor kan bli riktigt stora,
     som Körningar.
   - Vad söks: namn, ägare, taggar och beskrivning som i Biblioteket idag, eller all synlig text i raden?
5. Beskrivningarna: hyllornas, typernas meningar, Miljöns sektioner och sidornas underrubriker (som "Everything you work
   with, by kind…")? Förslaget: alla, på båda språken.
6. Det sista meddelandet slutade med ett ensamt "5.": var det något mer?
