import os
from typing import List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qdrant_client
from qdrant_client import QdrantClient
from cohere import ClientV2 as CohereClient
import logging
# from fastembed.sparse import SparseTextEmbedding, SparseEmbedding
from fastembed.text import TextEmbedding
import json
from fastapi.responses import StreamingResponse
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


text = "Almelo has a strategy in place to adapt to the effects of climate change, called the Almelose Klimaatadaptatiestrategie. The strategy was established in 2021 and will run until 2025. It aims to prepare the city for the effects of climate change, including water shortages, flooding, drought, and heat stress. \n\nThe strategy was developed with input from the city council and residents. It includes ambitions and guidelines to ensure the city remains accessible to emergency services during extreme weather events and to prevent damage to buildings and infrastructure from flooding. It also aims to improve the city's water resilience and provide cooling options to prevent heat stress for vulnerable groups. \n\nAlmelo has also established a subsidy scheme to encourage residents to implement climate adaptation measures on their properties, such as removing stone from gardens, rainwater storage, and the use of water barrels. \n\nIn addition to the adaptation strategy, Almelo is working on improving its energy efficiency. For example, the city has distributed energy-saving measures, such as sustainable lamps, draught excluders, and radiator foil, to over 5,000 homeowners. The city is also exploring the potential for wind energy in collaboration with neighbouring municipalities and the province of Overijssel."
    
citations = [
    {
    "start": 13,
    "end": 72,
    "text": "strategy in place to adapt to the effects of climate change",
    "sources": [
        {
        "type": "document",
        "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
        "document": {
            "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
            "location": "Almelo",
            "snippet": "groene waterstad met tal van projecten in de wijken. Dit alles past ook in de Almelose Klimaatadaptatiestrategie, zoals die in het voorjaar van 2021 door de raad is vastgesteld. Of realisatie van deze ambities uiteindelijk zal leiden tot een hogere positie in de Atlas voor gemeenten is echter de vraag, gezien de criteria van deze Atlas. Zo zal bijvoorbeeld de bereikbaarheid van Natura 2000 gebieden niet veranderen door Almeloos beleid. Wij gaan ervan uit u hiermee voldoende te hebben genformeerd. Hoogachtend, Burgemeester en wethouders van Almelo, de secretaris, de burgemeester, Pagina 2 van 2 UIT 23110086",
            "source_id": "36a8a854088eb8c00cd44fac7af702d6173a1744",
            "title": "Agendabundel",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F1756079"
        }
        },
        {
        "type": "document",
        "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
        "document": {
            "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
        "document": {
            "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
        "document": {
            "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
        "document": {
            "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 85,
    "end": 120,
    "text": "Almelose Klimaatadaptatiestrategie.",
    "sources": [
        {
        "type": "document",
        "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
        "document": {
            "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
            "location": "Almelo",
            "snippet": "groene waterstad met tal van projecten in de wijken. Dit alles past ook in de Almelose Klimaatadaptatiestrategie, zoals die in het voorjaar van 2021 door de raad is vastgesteld. Of realisatie van deze ambities uiteindelijk zal leiden tot een hogere positie in de Atlas voor gemeenten is echter de vraag, gezien de criteria van deze Atlas. Zo zal bijvoorbeeld de bereikbaarheid van Natura 2000 gebieden niet veranderen door Almeloos beleid. Wij gaan ervan uit u hiermee voldoende te hebben genformeerd. Hoogachtend, Burgemeester en wethouders van Almelo, de secretaris, de burgemeester, Pagina 2 van 2 UIT 23110086",
            "source_id": "36a8a854088eb8c00cd44fac7af702d6173a1744",
            "title": "Agendabundel",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F1756079"
        }
        },
        {
        "type": "document",
        "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
        "document": {
            "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
        "document": {
            "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
        "document": {
            "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
        "document": {
            "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 153,
    "end": 157,
    "text": "2021",
    "sources": [
        {
        "type": "document",
        "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
        "document": {
            "id": "6aa846a0-666d-5e3b-a9f4-c439993f884a",
            "location": "Almelo",
            "snippet": "groene waterstad met tal van projecten in de wijken. Dit alles past ook in de Almelose Klimaatadaptatiestrategie, zoals die in het voorjaar van 2021 door de raad is vastgesteld. Of realisatie van deze ambities uiteindelijk zal leiden tot een hogere positie in de Atlas voor gemeenten is echter de vraag, gezien de criteria van deze Atlas. Zo zal bijvoorbeeld de bereikbaarheid van Natura 2000 gebieden niet veranderen door Almeloos beleid. Wij gaan ervan uit u hiermee voldoende te hebben genformeerd. Hoogachtend, Burgemeester en wethouders van Almelo, de secretaris, de burgemeester, Pagina 2 van 2 UIT 23110086",
            "source_id": "36a8a854088eb8c00cd44fac7af702d6173a1744",
            "title": "Agendabundel",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F1756079"
        }
        },
        {
        "type": "document",
        "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
        "document": {
            "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
        "document": {
            "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
        "document": {
            "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
        "document": {
            "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        }
    ]
    },
    {
    "start": 177,
    "end": 182,
    "text": "2025.",
    "sources": [
        {
        "type": "document",
        "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
        "document": {
            "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
        "document": {
            "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
        "document": {
            "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
        "document": {
            "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 194,
    "end": 244,
    "text": "prepare the city for the effects of climate change",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 256,
    "end": 271,
    "text": "water shortages",
    "sources": [
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "30062fb7-af1d-5cdd-a8ad-3703f08a6a79",
        "document": {
            "id": "30062fb7-af1d-5cdd-a8ad-3703f08a6a79",
            "location": "Almelo",
            "snippet": "de klimaatadaptieve stad van 2075 in Twente. Een vergezicht dat nu al actueel is voor de inrichting van de steden. Almelo heeft een unieke ligging als het gaat om water. Een waterrijke invulling van stad en ommeland is noodzakelijk om te kunnen inspelen op de heftige neerslag die steeds vaker voorkomt. Tegelijkertijd biedt het water grote kansen voor de stad als het gaat om recreatie en toerisme en daarmee voor een aantrekkelijk centrum. Pagina 1 van 2 Raad 2307716 DCS 2382229",
            "source_id": "5b0bdd83431b18f86f660849a19441957cf6ed56",
            "title": "C.1 RB (7716) Jaarverslag stadsbouwmeester 2022.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9165"
        }
        }
    ]
    },
    {
    "start": 273,
    "end": 281,
    "text": "flooding",
    "sources": [
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 283,
    "end": 290,
    "text": "drought",
    "sources": [
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 296,
    "end": 308,
    "text": "heat stress.",
    "sources": [
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
        "document": {
            "id": "f3844f78-91c9-5c44-a533-4299c1d2dce1",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
        "document": {
            "id": "97b3cb10-e7a6-59a4-b1fe-25d72a9b4e26",
            "location": "Almelo",
            "snippet": "Inleiding In 2019 hebben we stresstesten uitgevoerd en zijn de effecten in beeld gebracht die worden veroorzaakt door het veranderende klimaat. Het gaat dan over overstroming, extreme regenval, droogte en hitte. Zie ook de raadsbrief \"Kwetsbaarheden irm klimaatverandering\" van 12 november 2019 met kenmerk Raad 1905732. De resultaten van deze stresstesten hebben we op 4 februari 2020 gepresenteerd in een politiek beraad beeldvormend en via een zogeheten \"klimaateffectenspel\" hebben de raadsleden ons leidende principes meegegeven om de effecten te kunnen prioriteren. Welke effecten van weersextremen zijn onacceptabel, welke zijn onwenselijk en welke zijn acceptabel? Deze principes zijn als basis gehanteerd voorde Almelose Klimaatadaptatiestrategie. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. We hebben in de eigen organisatie en via het project Almelo's klimaat in",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 343,
    "end": 385,
    "text": "input from the city council and residents.",
    "sources": [
        {
        "type": "document",
        "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
        "document": {
            "id": "f7b04c5f-f071-545a-a9ce-487a37dd0a6e",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
        "document": {
            "id": "5368e95a-d38b-5265-9f95-d1e048a1973d",
            "location": "Almelo",
            "snippet": "~err,~ent~ ~ ~ Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Raadsbesluit Onderwerp: Almelose Klimaatadaptatiestrategie 2021 2025 Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terrein en daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
        "document": {
            "id": "bd7a62fd-1b7d-565a-a4ac-f3561891d1b4",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
        "document": {
            "id": "a94c69e1-68a5-5a09-8b83-9e09a3042e31",
            "location": "Almelo",
            "snippet": "Raadsvergadering: 22 juni 2021 Registratienummer: R 2106642 Naam: M. Roordink Datum: 22 juni 2021 Team/teamonderdeel: ADV Advies Telefoonnummer: 541451 Voorstel aan de raad Onderwerp Almelose Klimaatadaptatiestrategie 2021 2025 Portefeuillehouder E.J.F.M. van Mierlo Samenvatting raadsvoorstel Het klimaat verandert en dat heeft effecten op de stad en onze dorpen. In de Almelose Klimaatadaptatiestrategie staat aangegeven hoe we in Almelo deze effecten willen aanpakken. Samen met de met inbreng van betrokken inwoners en organisaties hebben we daar een strategie voor opgesteld. De strategie bestaat uit een beschrijving van de problematiek, de te verwachten effecten, de ambitie en een uitvoeringsagenda met maatregelen die nodig zijn om klimaatrobuust te worden. Uiterlijk in 2030 lossen we alle onacceptabele situaties op. De onwenselijke situaties lossen we op door ze te combineren met andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 398,
    "end": 422,
    "text": "ambitions and guidelines",
    "sources": [
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 437,
    "end": 512,
    "text": "city remains accessible to emergency services during extreme weather events",
    "sources": [
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 520,
    "end": 581,
    "text": "prevent damage to buildings and infrastructure from flooding.",
    "sources": [
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 617,
    "end": 633,
    "text": "water resilience",
    "sources": [
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 646,
    "end": 707,
    "text": "cooling options to prevent heat stress for vulnerable groups.",
    "sources": [
        {
        "type": "document",
        "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
        "document": {
            "id": "0988cba7-c07e-5f02-b742-df8dde23b94a",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
        "document": {
            "id": "8f335058-9004-5bd0-8443-77a33f5a7779",
            "location": "Almelo",
            "snippet": "samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. De Raad van de Gemeente Almelo: Gezien het voorstel van burgemeester en wethouders; Besluit: 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit te voeren te kiezen voor: a. Uiterlijk in 2030 zijn alle",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        },
        {
        "type": "document",
        "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
        "document": {
            "id": "d3289145-d62e-52cf-a75c-9f2250c85065",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "3e874b87fb78ba8402ee0efd1d443d917870a1bf",
            "title": "10 Almelose Klimaatadaptatiestrategie 2021-2025 - Raadsbesluit (getekend).pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F6794"
        }
        },
        {
        "type": "document",
        "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
        "document": {
            "id": "e141c8ec-bf10-5b1d-8f08-86ca12a11da0",
            "location": "Almelo",
            "snippet": "et andere werkzaamheden (werk met werk maken). Klimaatadaptatie gaat ook over particulier terreinen daarom zetten we ook in op samenwerken en stimuleren om inwoners, bedrijven en corporaties te motiveren om ook hun steentje bij te dragen. Voorgesteld raadsbesluit 1. Kennis te nemen van de Almelose Klimaatadaptatiestrategie 2021 2025 (reg.nr. 02 intern 76832 20210504 Hoofdrapport) en Achtergrondrapport (reg.nr. 02 intern 76832 20210504 Achtergrondrapport) 2. In te stemmen met de volgende ambities en uitgangspunten: a. Bij extreme regenval blijven hoofd en gebiedsontsluitingswegen toegankelijk voor hulpdiensten; b. Regenval veroorzaakt geen grote schade in gebouwen of nutsvoorzieningen; c. Hoge grondwaterstanden veroorzaken geen schade of gezondheidsrisico's; d. Er zijn voldoende mogelijkheden voor verkoeling in de stad, om hittestress voor kwetsbare groepen en objecten te voorkomen; e. De sponswerking van de bodem is vergroot en we beschikken over een robuust watersysteem. 3. Voorde strategie om maatregelen uit",
            "source_id": "ecf727937611022320de1b67500574d3d729a0f1",
            "title": "4.3 Raadmeter 2021 - Bijlage 3 - Almelose Klimaatadaptatiestrategie 2021-2025.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20190809125121%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F4352138"
        }
        }
    ]
    },
    {
    "start": 740,
    "end": 754,
    "text": "subsidy scheme",
    "sources": [
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        },
        {
        "type": "document",
        "id": "443704db-1c03-51de-bd4a-cd05bf099203",
        "document": {
            "id": "443704db-1c03-51de-bd4a-cd05bf099203",
            "location": "Almelo",
            "snippet": "a. constructieve voorzieningen, zoals nieuwbouw of aanpassingen van dakconstructies en overkappingen; b. vervanging van bestaande beplanting en groen; c. kosten die verband houden met de eigen inzet of de inzet van eigen personeel van de aanvrager, waaronder gederfde inkomsten; d. kosten voor het opstellen en indienen van de subsidieaanvraag; e. maatregelen en bijkomende werkzaamheden zoals bijvoorbeeld een vijver, groene erfafscheiding, vergroenen balkon, kunstgras, houten vlonders, speeltoestellen, tuinadvies en tuinontwerp.",
            "source_id": "42d63ac8739349eba67b7c6a37165a60c2ac7c47",
            "title": "Subsidieregeling Klimaatmaatregelen Almelo 2022",
            "url": "https://aleph.openstate.eu/entities/697934.a785577dbb5f95ba32f68795f92afa496c8d599e"
        }
        }
    ]
    },
    {
    "start": 758,
    "end": 838,
    "text": "encourage residents to implement climate adaptation measures on their properties",
    "sources": [
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        }
    ]
    },
    {
    "start": 848,
    "end": 925,
    "text": "removing stone from gardens, rainwater storage, and the use of water barrels.",
    "sources": [
        {
        "type": "document",
        "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
        "document": {
            "id": "e82c12df-afd1-5292-ae3c-fcaad1eea56a",
            "location": "Almelo",
            "snippet": "emengd is met schoon water.  Wat doet Almelo om mensen te helpen op het gebruik van water te besparen? De gemeenteraad heeft op 22 juni 2021 de Almelose Klimaatadaptatiestrategie vastgesteld, om voorbereid te zijn op de effecten van de klimaatverandering op gebied van wateroverlast, hitte, droogte en waterveiligheid. Op basis hiervan is de gemeentelijke subsidieregeling Doe eens groen ingesteld, waarmee bewoners wordt gestimuleerd klimaatadaptieve maatregelen te treffen op eigen terrein. Zoals ontstenen van tuinen, berging van water, regentonnen etc. Bank: BNG Bank, Den Haag Pagina 1 van 2 NL56 BNGH 028 50 00 187 BTWnr. UIT 22105573 BIC Code: BNGHNL2G NL 0015 84 108 B 01",
            "source_id": "f8ec5dd7988b00829f69252585be83c9c4e1a3af",
            "title": "C.2 UIT (105573) Beantwoording schriftelijke vragen over water in Almelo.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F7266"
        }
        }
    ]
    },
    {
    "start": 989,
    "end": 1021,
    "text": "improving its energy efficiency.",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "277eb91c-cd42-5751-976c-d5827fc8439c",
        "document": {
            "id": "277eb91c-cd42-5751-976c-d5827fc8439c",
            "location": "Almelo",
            "snippet": "Programmaplan 2023 2026 | Klimaat en Milieu 15 In het programma werken we aan lange termijn doelen. Om de gewenste beweging te krijgen, hanteert Almelo vijf strategien. De opbouw van de vijf strategien gaat uit van een steeds groter ingrijpen in de leefomgeving, maar de stappen hoeven niet noodzakelijkerwijs in deze volgrode uitgevoerd te worden. Strategie 1: bewustzijn creren Deze strategie is erop gericht dat inwoners, bedrijven, instellingen en onze eigen organisatie zich be wust zijn dat klimaatverandering om actie vraagt en dat zij daar zelf aan bij kunnen dragen. Acties om risicos van klimaatverandering te beperken en acties richting een andere energievoorziening en een circulaire economie. Ze weten wat ze zelf kunnen doen om risicos te beperken en kansen te benutten. Strategie 2: netwerken bouwen Veel van de doelen liggen niet of maar gedeeltelijk binnen de directe invloedsfeer van de gemeente. Om onze invloedsfeer te vergroten of te gebruiken, bouwen we (mee aan) netwerken met inwoners,",
            "source_id": "41c001bc3bf3c0e058b4f019b8d4e1c639d3971b",
            "title": "20230217 - INT (86076) ALM2301003 P_Programma Klimaat en milieu lr4 v0215.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9328"
        }
        }
    ]
    },
    {
    "start": 1060,
    "end": 1082,
    "text": "energy-saving measures",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        }
    ]
    },
    {
    "start": 1092,
    "end": 1147,
    "text": "sustainable lamps, draught excluders, and radiator foil",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        }
    ]
    },
    {
    "start": 1152,
    "end": 1174,
    "text": "over 5,000 homeowners.",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        }
    ]
    },
    {
    "start": 1192,
    "end": 1231,
    "text": "exploring the potential for wind energy",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        },
        {
        "type": "document",
        "id": "5c40a4e1-dfac-5250-ab49-0ccb3084013d",
        "document": {
            "id": "5c40a4e1-dfac-5250-ab49-0ccb3084013d",
            "location": "Almelo",
            "snippet": "de gemeenten Almelo, Enschede en Hengelo, waterschap Vechtstromen en provincie Overijssel de krachten gebundeld. De rode draden uit de 'Klimaatagenda: weerbaar, welvarend en groen' zijn als uitgangspunten genomen: Mitigatie: maatregelen die bijdragen aan de beperking van de klimaatverandering; Juist in de stad liggen er veel kansen om bij te dragen aan beperking van de klimaatverandering. Met al haar stromen van mensen, energie, voedsel en producten werkt ze mee aan de uitstoot van broeikasgassen. Ze heeft daarom een belangrijke taak in het vinden van slimme oplossingen voor transport, consumptie, verwarming en koeling. Dat vraagt naast andere gebouwen en installaties ook om een andere inrichting van de stad. Watergerichte maatregelen wijzen de weg: afkoppeling van hemelwater reduceert het energiegebruik van rioolwaterzuiverings installaties, koudewinning is een adequaat (en lucratief!) alternatief voor airconditioning, terwijl groene daken en bomen garant staan voor natuurlijke koeling en opname van CO2.",
            "source_id": "26c89f2901aad5e9d8744097e11b67239911937c",
            "title": "C.4 INT (75642) CompleetAnaloog_NL.IMRO.0141.00101-BP21.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F10058"
        }
        },
        {
        "type": "document",
        "id": "da8d79f8-1b44-5735-98c4-af317827d308",
        "document": {
            "id": "da8d79f8-1b44-5735-98c4-af317827d308",
            "location": "Almelo",
            "snippet": "· te benutten als tijdelijke berging. Hiervoor moet de infrastructuur waterbewust en klimaatbestendig worden ingericht. Hierbij kan worden gedacht aan niet te lage vloerpeilen, het toepassen van trottoirbanden langs de wegen en het afvoeren van alle dakoppervlak naar de voorzijde van de woning Klimaat actieve stad Als KlimaatActieve Stad Twente, kortweg KAS, hebben de gemeenten Almelo, Enschede en Hengelo, waterschap Vechtstromen en provincie Overijssel de krachten gebundeld. De rode draden uit de Klimaatagenda: weerbaar, welvarend en groen zijn als uitgangspunten genomen:  Mitigatie: maatregelen die bijdragen aan de beperking van de klimaatverandering; Juist in de stad liggen er veel kansen om bij te dragen aan beperking van de klimaatverandering. Met al haar stromen van mensen, energie, voedsel en producten werkt ze mee aan de uitstoot van broeikasgassen. Ze heeft daarom een belangrijke taak in het vinden van slimme oplossingen voor transport, consumptie, verwarming en koeling. Dat vraagt naast andere",
            "source_id": "b9680f82fe133d881a57ef662b5eb9d59f6d902d",
            "title": "Concept bestemmingsplan Haven Zuid e.o.",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F1628837"
        }
        }
    ]
    },
    {
    "start": 1235,
    "end": 1313,
    "text": "collaboration with neighbouring municipalities and the province of Overijssel.",
    "sources": [
        {
        "type": "document",
        "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
        "document": {
            "id": "3d6f5cfe-596f-52ac-ba13-072809b36336",
            "location": "Almelo",
            "snippet": "arende maatregelen. Ruim 5.000 woningeigenaren hebben voor 50 euro aan kleine energiebesparende maatregelen ontvangen. Denk aan duurzame lampen, tochtstrippen en radiatorfolie. Samen met de buurgemeenten Tubbergen en Twenterand en de provincie Overijssel werkt Almelo aan een verkenning naar de mogelijkheden voor windenergie. De samenwerking zorgt voor afstemming op het gebied van ruimtelijke en technische (on)mogelijkheden en een eenduidige communicatie naar inwoners van het gebied. In mei 2021 is de Almelose Klimaatadaptatiestrategie vastgesteld. Het geeft duidelijkheid over de gevolgen van Klimaatverandering voor Almelo en de stappen die Almelo zet om zich daarop voor te bereiden. De voorbereidingen voor de stimuleringsregeling zijn opgestart. Pagina 2 van 9",
            "source_id": "bfae79565bce59bbb7d5210abbb15414c5d037da",
            "title": "C.6 RB (7130) Jaarverantwoording 2021 op hoofdlijnen.pdf",
            "url": "https://openbesluitvorming.nl/?zoekterm=%22*%22&organisaties=%5B%22ori_almelo_20230705020852%22%5D&showResource=https%253A%252F%252Fid.openraadsinformatie.nl%252F9646"
        }
        }
    ]
    }
    ]        
    


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,    
    allow_origins=[
        "http://localhost:5173", 
        "http://0.0.0.0:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:8000", 
        "http://0.0.0.0:8000", 
        "http://127.0.0.1:8000", 
        "http://dl:8000",
        "http://bron.ngrok.app", 
        "https://bron.ngrok.app", 
        "http://bron.ngrok.app:5173", 
        "https://bron.ngrok.app:5173", 
        "http://bron.ngrok.app:8000", 
        "https://bron.ngrok.app:8000", 
        "http://bron.ngrok.io", 
        "https://bron.ngrok.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize clients
# qdrant_client = QdrantClient(os.getenv("QDRANT_URL"))
qdrant_client = QdrantClient(host="host.docker.internal", port=6333)
cohere_client = CohereClient(api_key=os.getenv("COHERE_API_KEY"))

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    content: str

async def retrieve_relevant_documents(query: str) -> List[Dict]:  
    logger.info(f"Retrieving relevant documents for query: {query}")
    # Get documents from Qdrant
    qdrant_documents = get_bron_documents_from_qdrant(
        cohere_client=cohere_client,
        query=query, 
        limit=100
    )

    # Rerank documents using Cohere
    if qdrant_documents is not None and len(qdrant_documents) > 0:
        logger.info(f"Documents: {qdrant_documents[0]}")
        # convert Qdrant ScoredPoint to Cohere RerankDocument
        document_texts = [document.payload['content'] for document in qdrant_documents]
        reranked_documents = cohere_client.rerank(
            query = query,
            documents = document_texts,
            top_n = 20,
            model = 'rerank-multilingual-v3.0',
            return_documents=True
        )
        
        qdrant_documents = [qdrant_documents[result.index] for result in reranked_documents.results]           
            
    return [ 
        { 
            'id': f'{doc.id}',
            'data': { 
                'source_id': doc.payload['meta']['source_id'],
                'url': doc.payload['meta']['url'],
                'title': doc.payload['meta']['title'],
                'location': doc.payload['meta']['location_name'],
                'snippet': doc.payload['content'] 
            } 
        } for doc in qdrant_documents 
    ]  
  
models_dir = os.path.join(os.path.dirname(__file__), 'models')

# sparse_document_embedder_0 = SparseTextEmbedding(
#     cache_dir=models_dir,
#     model_name="Qdrant/bm25",
#     providers=[("CUDAExecutionProvider", {"device_id": 0})]
# )

# def generate_sparse_vector(query):
#     logger.info(f"Generating sparse vector for query: {query}")
#     return sparse_document_embedder_0.embed(query)
    
def get_bron_documents_from_qdrant(cohere_client, query, limit=50):   
    logger.info(f"Retrieving documents from Qdrant for query: {query}")
    try:
        # Generate dense embedding
        dense_vector = cohere_client.embed(
            texts=[query], 
            input_type="search_query", 
            model="embed-multilingual-light-v3.0",
            embedding_types=["float"]
        ).embeddings.float[0]
    except Exception as e:
        logger.error(f"Error creating dense vector from query using Cohere: {e}")
        return None
            
    try:
        qdrant_documents = qdrant_client.search(
            query_vector=("text-dense", dense_vector),
            collection_name="1_gemeente_cohere",            
            limit=limit   
        )
        
        return qdrant_documents    
    except Exception as e:
        logger.error(f"Error retrieving documents from Qdrant: {e}")   
        return None

async def generate_response(messages: List[ChatMessage], relevant_docs: List[Dict]):    
    logger.info(f"Generating response for messages and documents: {messages}")
    system_message = ChatMessage(role="system", content="Antwoordt altijd in het Nederlands.")
    messages = [system_message] + messages
    response = cohere_client.chat(
        model="command-r-plus",
        messages=messages,
        documents=relevant_docs
    )
    # logger.info(f"Response: {response}")
    return response

async def generate_initial_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating initial response for query: {query}")
    initial_response = {
        "type": "initial",
        "role": "assistant",
        "documents": relevant_docs,
        "content": "Rechts vast de relevante documenten. Bron genereert nu een antwoord op uw vraag...",
        "content_original": "Rechts vast de relevante documenten. Bron genereert nu een antwoord op uw vraag..."
    }
    return json.dumps(initial_response) + "\n"

async def generate_full_response(query: str, relevant_docs: List[Dict]):
    logger.info(f"Generating full response for query: {query}")
    llm_response = await generate_response([ChatMessage(role="user", content=query)], relevant_docs)
    
    text = llm_response.message.content[0].text
    citations = llm_response.message.citations
    
    # logger.info(f"LLM response: {llm_response}")
    
    # text_w_citations = text    
    processed_citations = []
    text_formatted = text
    if citations:
        for citation in citations:
            processed_citation = {
                'start': citation.start,
                'end': citation.end,
                'text': citation.text,
                'document_ids': [source.document['id'] for source in citation.sources]
            }
            processed_citations.append(processed_citation)
    
        text_formatted = format_text_with_citations(text, processed_citations)

    # text_formatted = text
    # processed_citations = []
    # if citations:
    #     for citation in citations:
    #         processed_citation = {
    #             'start': citation['start'],
    #             'end': citation['end'],
    #             'text': citation['text'],
    #             'document_ids': [source['document']['id'] for source in citation['sources']]
    #         }
    #         processed_citations.append(processed_citation)
    
    #     # logger.info(f"Citations: {processed_citations}")
    
    #     text_formatted = format_text_with_citations(text, processed_citations)
            
    full_response = {
        "type": "full",
        "role": "assistant",
        "content": text_formatted,
        "content_original": text,
        "citations": processed_citations
    }
    
    return json.dumps(full_response) + "\n"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Received chat request: {request.content}")
    try:
        query = request.content
        
        async def response_generator():
            relevant_docs = await retrieve_relevant_documents(query)
            
            # Send initial response
            initial_response = await generate_initial_response(query, relevant_docs)
            yield initial_response
            await asyncio.sleep(0)  # Ensure the initial response is flushed
            
            # Send full response
            full_response = await generate_full_response(query, relevant_docs)
            yield full_response
        
        return StreamingResponse(
            response_generator(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"}  # Disable nginx buffering if you're using it
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {"error": "An error occurred while processing your request."}

@app.get("/api/documents")
async def documents_endpoint():
    query = "klimaat almelo"
    relevant_docs = await retrieve_relevant_documents(query)
    return {"documents": relevant_docs}

# @app.get("/")
# async def root():
#     return {"message": "Hello Worlds"}

def format_text_with_citations(text, citations):
    citations_list = sorted(citations, key=lambda x: x['start'])
    
    text_w_citations = ""
    last_end = 0
    footnotes = []
    
    for i, citation in enumerate(citations_list, start=1):
        # Add text before the citation
        text_w_citations += text[last_end:citation['start']]
        
        # Add the citation
        citation_text = text[citation['start']:citation['end']] 
        document_id_list_string = ','.join([f"'{doc_id}'" for doc_id in citation['document_ids']])
        text_w_citations += f'<span class="citation-link" data-document-ids="[{document_id_list_string}]">{citation_text}</span>'                
        last_end = citation['end']
    
    # Add any remaining text after the last citation
    text_w_citations += text[last_end:]    
    
    return text_w_citations
