Az InTracker egy AI-first, fejlesztőközpontú projekt- és ötletmenedzsment rendszer, amelynek célja, hogy az ötletektől indulva strukturált projekteken keresztül egészen a megvalósításig vezesse a munkát – úgy, hogy közben a fejlesztő és az AI (pl. Cursor) ugyanabból a valós projektállapotból dolgozzon.

⸻

1. Rendszer célja és filozófiája

Az InTracker nem klasszikus projektmenedzsment eszköz.
Nem időalapú tervezésre, nem riportolásra és nem „management dashboardokra” épül, hanem:
	•	kontekztusmegőrzésre
	•	projektek közötti gyors váltásra
	•	AI-val való együttműködésre
	•	strukturált gondolkodásra

Az alapfeltevés az, hogy a legnagyobb veszteség fejlesztés közben nem a kódolási idő, hanem a kontextus elvesztése. Az InTracker ezt csökkenti minimálisra.

⸻

2. Alap fogalmak és entitások

Ötlet (Idea)

Egy kezdeti gondolat, probléma vagy koncepció.
Lehet:
	•	nyers jegyzet,
	•	félig kidolgozott elképzelés,
	•	vagy már majdnem projekt.

Az ötlet egy kattintással projektté alakítható, előre definiált vagy egyedi struktúrával.

⸻

Projekt (Project)

A projekt az InTracker legfelső szintű egysége.
Egy projekt tartalmazza:
	•	a teljes struktúrát (hierarchia)
	•	az aktuális állapotot
	•	a döntéseket
	•	a dokumentációt
	•	az aktív munkameneteket
	•	a GitHub-kapcsolatokat
	•	az AI-nak szánt kontextust

Minden projekt önálló „világ”, de az InTracker lehetővé teszi a projektek közötti keresztkapcsolatokat és címkézést.

⸻

Projekt elem (Project Element)

A projekt elemei hierarchikusan épülnek fel. Egy elem lehet például:
	•	modul
	•	feature
	•	komponens
	•	mérföldkő
	•	technikai blokk
	•	döntési pont

Minden projekt elemhez tartozhat:
	•	leírás (mit, miért, hogyan)
	•	státusz (todo / in progress / blocked / done)
	•	függőségek
	•	todo-lista
	•	dokumentumok
	•	Definition of Done
	•	GitHub-hivatkozások

⸻

Todo (Task / Todo Item)

A projekt elemekhez tartozó konkrét lépések.
Nem sprint-alapúak, hanem logikai haladást követnek.

Egy todo rendelkezhet:
	•	állapottal
	•	becsült ráfordítással
	•	blokkoló tényezővel
	•	GitHub issue / PR kapcsolattal

⸻

Dokumentáció (Docs)

Az InTrackerben a dokumentáció nem wiki, hanem projektmemória.

Tipikus dokumentumtípusok:
	•	Architecture snapshot
	•	Decision log (ADR)
	•	Domain / fogalomtár
	•	Constraints (mit nem szabad)
	•	Runbook (build, run, deploy)
	•	AI instruction / working rules

A dokumentumok:
	•	rövidek,
	•	strukturáltak,
	•	feladatokból és elemekből hivatkozhatók,
	•	MCP-n keresztül elérhetők az AI számára.

⸻

Session (Munkamenet)

Az InTracker egyik kulcsfogalma.

Egy session:
	•	egy konkrét fejlesztési időszakot reprezentál
	•	tartalmaz célt, lépéseket és elvárt outputot
	•	a végén automatikusan készül egy session summary

Ez a summary lesz a következő belépési pont, amikor a projektbe visszatérsz.

⸻

3. Projektváltás és kontextuskezelés

Minden projekt rendelkezik egy Resume Context csomaggal:
	•	Last: mit csináltunk legutóbb
	•	Now: mi a következő 1–3 lépés
	•	Next blockers: mi akadályozhat
	•	Constraints: fontos szabályok
	•	Cursor instructions: hogyan dolgozzon az AI ezen a projekten

Ez teszi lehetővé, hogy projektről projektre 1–3 perc alatt vissza lehessen rázódni.

⸻

4. MCP szerver – AI integráció

Az InTracker része egy Model Context Protocol (MCP) szerver, amelyen keresztül az AI (pl. Cursor):
	•	lekérdezheti a projekt aktuális állapotát
	•	megkaphatja a teljes kontextuscsomagot
	•	todo-kat hozhat létre vagy frissíthet
	•	session summaryt készíthet
	•	dokumentációkat olvashat
	•	GitHub-kapcsolatokat kezelhet

Az AI így nem találgat, hanem a projekt valós állapotából dolgozik.

⸻

5. GitHub integráció

Az InTracker és a GitHub között kétirányú kapcsolat van:
	•	projekt elem ↔ GitHub issue
	•	todo ↔ PR
	•	commit ↔ projekt kontextus

A fejlesztés állapota visszacsatolódik az InTrackerbe, a projektterv pedig nem szakad el a kódtól.

⸻

6. Több projekt kezelése

Az InTracker támogatja:
	•	több aktív projekt párhuzamos futtatását
	•	státusz szerinti szűrést (active / paused / blocked)
	•	cross-project keresést
	•	címkéket és technológiai kategóriákat

Ez lehetővé teszi, hogy több, akár 5–12 projekt is kontroll alatt maradjon, kontextusvesztés nélkül.

⸻

7. Tudatosan kihagyott funkciók

Az InTracker szándékosan nem tartalmaz:
	•	Gantt chartokat
	•	túlzott időnyilvántartást
	•	menedzsment-reportokat
	•	chat-alapú task kommentelést

A fókusz a gondolkodáson, struktúrán és haladáson van.

⸻

8. Összkép

Az InTracker egy olyan rendszer, ahol:
	•	az ötlet nem vész el,
	•	a projekt nem esik szét,
	•	a dokumentáció él,
	•	az AI nem kódbuborékban dolgozik,
	•	a fejlesztő pedig gyorsan tud váltani, fókuszálni és haladni.

InTracker = strukturált gondolkodás + projektmemória + AI-kompatibilis kivitelezés.