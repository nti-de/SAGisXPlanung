<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<!--
  https://gitlab.opencode.de/xleitstelle/xplanung/testdaten/-/blob/main/valide/6_0/bp/BPlan001_6-0.gml?ref_type=heads
  Testfälle:
  - BP_KomplexeZweckbestGruen
  - BP_VeraenderungssperreDaten
  - XP_VerbundenerPlanBereich
  - Besondere Zweckbestimmung in SO_Strassenverkehr
-->
<xplan:XPlanAuszug xmlns:xplan="http://www.xplanung.de/xplangml/6/0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:wfs="http://www.opengis.net/wfs" gml:id="GML_c0490d13-8f76-4583-b348-56957aad0813" xsi:schemaLocation="http://www.xplanung.de/xplangml/6/0 https://repository.gdi-de.org/schemas/de.xleitstelle.xplanung/6.0/XPlanung-Operationen.xsd">
  <gml:boundedBy>
    <gml:Envelope srsName="EPSG:25832">
      <gml:lowerCorner>564984.128 5940442.486</gml:lowerCorner>
      <gml:upperCorner>565072.441 5940522.630</gml:upperCorner>
    </gml:Envelope>
  </gml:boundedBy>
  <gml:featureMember>
    <xplan:BP_Plan gml:id="GML_bf2168c4-c292-4340-bc50-7a2aa2cab5be">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940442.486</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940522.630</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:name>BPlan001_6-0</xplan:name>
      <xplan:beschreibung>Testdaten</xplan:beschreibung>
      <xplan:technHerstellDatum>2021-07-01</xplan:technHerstellDatum>
      <xplan:wurdeGeaendertVonPlanBereich>
        <xplan:XP_VerbundenerPlanBereich>
          <xplan:planName>Testplan_Aend</xplan:planName>
          <xplan:aenderungsArt>10001</xplan:aenderungsArt>
          <xplan:aenderungsdatum>2018-04-03</xplan:aenderungsdatum>
          <xplan:bereichNummer>0</xplan:bereichNummer>
        </xplan:XP_VerbundenerPlanBereich>
      </xplan:wurdeGeaendertVonPlanBereich>
      <xplan:erstellungsMassstab>1000</xplan:erstellungsMassstab>
      <xplan:raeumlicherGeltungsbereich>
        <gml:MultiSurface srsName="EPSG:25832" gml:id="GML_a4b76c05-e841-441f-9284-0d28c0bd2502">
          <gml:surfaceMember>
            <gml:Polygon srsName="EPSG:25832" gml:id="GML_63208495-2dad-4690-a072-f31868f7eece">
              <gml:exterior>
                <gml:LinearRing>
                  <gml:posList srsDimension="2" count="5">564984.128 5940442.486 565072.441 5940442.486 565072.441 5940522.630 564984.128 5940522.630 564984.128 5940442.486 </gml:posList>
                </gml:LinearRing>
              </gml:exterior>
            </gml:Polygon>
          </gml:surfaceMember>
        </gml:MultiSurface>
      </xplan:raeumlicherGeltungsbereich>
      <xplan:gemeinde>
        <xplan:XP_Gemeinde>
          <xplan:ags>02000000</xplan:ags>
          <xplan:gemeindeName>Freie und Hansestadt Hamburg</xplan:gemeindeName>
        </xplan:XP_Gemeinde>
      </xplan:gemeinde>
      <xplan:planArt>10002</xplan:planArt>
      <xplan:rechtsstand>3000</xplan:rechtsstand>
      <xplan:veraenderungssperre>
        <xplan:BP_VeraenderungssperreDaten>
          <xplan:startDatum>2021-07-02</xplan:startDatum>
          <xplan:endDatum>2021-08-01</xplan:endDatum>
          <xplan:verlaengerung>1000</xplan:verlaengerung>
        </xplan:BP_VeraenderungssperreDaten>
      </xplan:veraenderungssperre>
      <xplan:staedtebaulicherVertrag>false</xplan:staedtebaulicherVertrag>
      <xplan:erschliessungsVertrag>false</xplan:erschliessungsVertrag>
      <xplan:durchfuehrungsVertrag>false</xplan:durchfuehrungsVertrag>
      <xplan:gruenordnungsplan>false</xplan:gruenordnungsplan>
      <xplan:bereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
    </xplan:BP_Plan>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_Bereich gml:id="GML_95a8b21b-8754-4350-9041-213259262fd8">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940442.486</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940511.714</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:nummer>0</xplan:nummer>
      <xplan:planinhalt xlink:href="#GML_51e17233-d921-46cb-83b9-af28451186a1" />
      <xplan:planinhalt xlink:href="#GML_fa0eea57-ebb1-4d50-b205-95865d6b9284" />
      <xplan:planinhalt xlink:href="#GML_b5f66983-6732-4cdc-8910-ba4d40a060e8" />
      <xplan:planinhalt xlink:href="#GML_06f9b5b2-8051-4f03-9dc3-50ba956a2670" />
      <xplan:planinhalt xlink:href="#GML_3b987a05-5df3-42ed-ba22-b1b04bf58bf0" />
      <xplan:planinhalt xlink:href="#GML_eb8753e9-db57-4f81-b9dd-37fc38fb4419" />
      <xplan:planinhalt xlink:href="#GML_c8fa8ddd-d5de-4111-9489-03967eec715e" />
      <xplan:praesentationsobjekt xlink:href="#GML_a81f7f4e-071f-44fd-af3e-826e80b82ee3" />
      <xplan:praesentationsobjekt xlink:href="#GML_458852b4-0f35-4405-b3be-90bb70688ddd" />
      <xplan:praesentationsobjekt xlink:href="#GML_a630c212-8ae0-4be6-91c4-b0dc8cba820a" />
      <xplan:praesentationsobjekt xlink:href="#GML_22989f35-59e8-4260-8c60-e706b916a886" />
      <xplan:verfahren>1000</xplan:verfahren>
      <xplan:gehoertZuPlan xlink:href="#GML_bf2168c4-c292-4340-bc50-7a2aa2cab5be" />
    </xplan:BP_Bereich>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_WohngebaeudeFlaeche gml:id="GML_51e17233-d921-46cb-83b9-af28451186a1">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565011.438 5940447.733</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940511.714</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:wirdDargestelltDurch xlink:href="#GML_22989f35-59e8-4260-8c60-e706b916a886" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_2ada5f26-230c-4dfe-ac97-f62ba56a6f3c">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="15">565065.689 5940482.457 565064.406 5940485.989 565055.484 5940510.564 565050.619 5940511.714 565048.163 5940509.388 565024.500 5940486.984 565011.438 5940474.619 565016.424 5940469.350 565020.516 5940465.024 565028.611 5940456.469 565029.337 5940457.156 565038.252 5940447.733 565053.250 5940456.591 565072.441 5940463.556 565065.689 5940482.457 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:typ>1000</xplan:typ>
    </xplan:BP_WohngebaeudeFlaeche>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_GruenFlaeche gml:id="GML_fa0eea57-ebb1-4d50-b205-95865d6b9284">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940468.040</gml:lowerCorner>
          <gml:upperCorner>565042.005 5940522.630</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_1c92b1db-bd5f-478c-a034-3b5e7bf9a81f">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="5">565042.005 5940522.630 564984.128 5940522.630 564984.128 5940468.040 565022.175 5940504.055 565042.005 5940522.630 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:zweckbestimmung>
        <xplan:BP_KomplexeZweckbestGruen>
          <xplan:allgemein>2700</xplan:allgemein>
          <xplan:detail>2400_10</xplan:detail>
          <xplan:aufschrift>Grüne Hölle</xplan:aufschrift>
        </xplan:BP_KomplexeZweckbestGruen>
      </xplan:zweckbestimmung>
      <xplan:nutzungsform>2000</xplan:nutzungsform>
    </xplan:BP_GruenFlaeche>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_BaugebietsTeilFlaeche gml:id="GML_b5f66983-6732-4cdc-8910-ba4d40a060e8">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940442.486</gml:lowerCorner>
          <gml:upperCorner>565038.252 5940474.619</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:wirdDargestelltDurch xlink:href="#GML_a630c212-8ae0-4be6-91c4-b0dc8cba820a" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_9315e58c-ee79-4e4a-85fa-993709ccfc29">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="12">565029.337 5940457.156 565028.611 5940456.469 565020.516 5940465.024 565016.424 5940469.350 565011.438 5940474.619 564999.828 5940463.629 564988.215 5940452.640 564984.128 5940448.773 564984.128 5940442.486 565034.802 5940442.486 565038.252 5940447.733 565029.337 5940457.156 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:besondereArtDerBaulNutzung>1450</xplan:besondereArtDerBaulNutzung>
    </xplan:BP_BaugebietsTeilFlaeche>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:SO_Strassenverkehr gml:id="GML_06f9b5b2-8051-4f03-9dc3-50ba956a2670">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940448.773</gml:lowerCorner>
          <gml:upperCorner>565055.484 5940522.630</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_7f6be5de-9acd-42b6-a664-1e8de042e532">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="13">565048.163 5940509.388 565050.619 5940511.714 565055.484 5940510.564 565045.164 5940522.630 565042.005 5940522.630 565022.175 5940504.055 564984.128 5940468.040 564984.128 5940448.773 564988.215 5940452.640 564999.828 5940463.629 565011.438 5940474.619 565024.500 5940486.984 565048.163 5940509.388 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:nordwinkel uom="grad">0.000000</xplan:nordwinkel>
      <xplan:artDerFestlegung>
        <xplan:SO_KomplexeZweckbestStrassenverkehr>
          <xplan:allgemein>3500</xplan:allgemein>
        </xplan:SO_KomplexeZweckbestStrassenverkehr>
      </xplan:artDerFestlegung>
      <xplan:nutzungsform>2000</xplan:nutzungsform>
      <xplan:hatDarstellungMitBesondZweckbest>true</xplan:hatDarstellungMitBesondZweckbest>
    </xplan:SO_Strassenverkehr>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_GruenFlaeche gml:id="GML_3b987a05-5df3-42ed-ba22-b1b04bf58bf0">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565045.164 5940463.858</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940522.630</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_27b9cf2e-4f08-4db9-9be5-9edd59ad5f0e">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="7">565072.441 5940522.630 565045.164 5940522.630 565055.484 5940510.564 565064.406 5940485.989 565065.689 5940482.457 565072.441 5940463.556 565072.441 5940522.630 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:zweckbestimmung>
        <xplan:BP_KomplexeZweckbestGruen>
          <xplan:allgemein>2700</xplan:allgemein>
          <xplan:detail>2400_10</xplan:detail>
        </xplan:BP_KomplexeZweckbestGruen>
      </xplan:zweckbestimmung>
      <xplan:nutzungsform>1000</xplan:nutzungsform>
    </xplan:BP_GruenFlaeche>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:BP_BaugebietsTeilFlaeche gml:id="GML_eb8753e9-db57-4f81-b9dd-37fc38fb4419">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565034.802 5940442.486</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940463.556</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:ebene>0</xplan:ebene>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:wirdDargestelltDurch xlink:href="#GML_458852b4-0f35-4405-b3be-90bb70688ddd" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_fd59b568-132d-4ff7-9549-d387f8c629d1">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="6">565072.441 5940463.556 565053.250 5940456.591 565038.252 5940447.733 565034.802 5940442.486 565072.441 5940442.486 565072.441 5940463.556 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>true</xplan:flaechenschluss>
      <xplan:besondereArtDerBaulNutzung>1700</xplan:besondereArtDerBaulNutzung>
    </xplan:BP_BaugebietsTeilFlaeche>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:SO_Gebiet gml:id="GML_c8fa8ddd-d5de-4111-9489-03967eec715e">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>564984.128 5940442.486</gml:lowerCorner>
          <gml:upperCorner>565072.441 5940511.714</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:wirdDargestelltDurch xlink:href="#GML_a81f7f4e-071f-44fd-af3e-826e80b82ee3" />
      <xplan:rechtscharakter>1000</xplan:rechtscharakter>
      <xplan:position>
        <gml:Polygon srsName="EPSG:25832" gml:id="GML_bb3db696-52cd-49d6-96fb-034ab3e910da">
          <gml:exterior>
            <gml:LinearRing>
              <gml:posList srsDimension="2" count="16">565065.689 5940482.457 565064.406 5940485.989 565055.484 5940510.564 565050.619 5940511.714 565048.163 5940509.388 565024.500 5940486.984 565011.438 5940474.619 564999.828 5940463.629 564988.215 5940452.640 564984.128 5940448.773 564984.128 5940442.486 565034.802 5940442.486 565038.252 5940447.733 565053.250 5940456.591 565072.441 5940463.556 565065.689 5940482.457 </gml:posList>
            </gml:LinearRing>
          </gml:exterior>
        </gml:Polygon>
      </xplan:position>
      <xplan:flaechenschluss>false</xplan:flaechenschluss>
      <xplan:gemeinde>
        <xplan:XP_Gemeinde>
          <xplan:ags>02000000</xplan:ags>
          <xplan:gemeindeName>Freie und Hansestadt Hamburg</xplan:gemeindeName>
        </xplan:XP_Gemeinde>
      </xplan:gemeinde>
      <xplan:gebietsArt>2400</xplan:gebietsArt>
    </xplan:SO_Gebiet>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:XP_PPO gml:id="GML_a81f7f4e-071f-44fd-af3e-826e80b82ee3">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565027.244 5940470.916</gml:lowerCorner>
          <gml:upperCorner>565028.244 5940471.916</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:art>xplan:gebietsArt</xplan:art>
      <xplan:art>xplan:gemeinde[1]/xplan:XP_Gemeinde/xplan:gemeindeName</xplan:art>
      <xplan:art>gemeinde[1]/XP_Gemeinde/ags</xplan:art>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:dientZurDarstellungVon xlink:href="#GML_c8fa8ddd-d5de-4111-9489-03967eec715e" />
      <xplan:position>
        <gml:Point srsName="EPSG:25832" gml:id="GML_9c0ff9d5-5736-4e21-a30c-ee5c459f7c78">
          <gml:pos>565027.244 5940470.916</gml:pos>
        </gml:Point>
      </xplan:position>
      <xplan:drehwinkel uom="grad">0.00</xplan:drehwinkel>
      <xplan:skalierung>1</xplan:skalierung>
    </xplan:XP_PPO>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:XP_PPO gml:id="GML_458852b4-0f35-4405-b3be-90bb70688ddd">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565063.749 5940451.169</gml:lowerCorner>
          <gml:upperCorner>565064.749 5940451.169</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:art>xplan:besondereArtDerBaulNutzung</xplan:art>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:dientZurDarstellungVon xlink:href="#GML_eb8753e9-db57-4f81-b9dd-37fc38fb4419" />
      <xplan:position>
        <gml:Point srsName="EPSG:25832" gml:id="GML_51c5093a-5964-41f6-8f3a-a07973982464">
          <gml:pos>565063.749 5940451.169</gml:pos>
        </gml:Point>
      </xplan:position>
      <xplan:drehwinkel uom="grad">0.0</xplan:drehwinkel>
      <xplan:skalierung>1.0</xplan:skalierung>
    </xplan:XP_PPO>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:XP_PPO gml:id="GML_a630c212-8ae0-4be6-91c4-b0dc8cba820a">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565010.917 5940455.804</gml:lowerCorner>
          <gml:upperCorner>565011.917 5940455.804</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:art>xplan:besondereArtDerBaulNutzung</xplan:art>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:dientZurDarstellungVon xlink:href="#GML_b5f66983-6732-4cdc-8910-ba4d40a060e8" />
      <xplan:position>
        <gml:Point srsName="EPSG:25832" gml:id="GML_3424ae3a-6635-45ac-9242-3089daeaf9db">
          <gml:pos>565010.917 5940455.804</gml:pos>
        </gml:Point>
      </xplan:position>
      <xplan:drehwinkel uom="grad">0.0</xplan:drehwinkel>
      <xplan:skalierung>1.0</xplan:skalierung>
    </xplan:XP_PPO>
  </gml:featureMember>
  <gml:featureMember>
    <xplan:XP_PPO gml:id="GML_22989f35-59e8-4260-8c60-e706b916a886">
      <gml:boundedBy>
        <gml:Envelope srsName="EPSG:25832">
          <gml:lowerCorner>565043.676 5940476.202</gml:lowerCorner>
          <gml:upperCorner>565044.676 5940476.202</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      <xplan:art>xplan:besondereArtDerBaulNutzung</xplan:art>
      <xplan:gehoertZuBereich xlink:href="#GML_95a8b21b-8754-4350-9041-213259262fd8" />
      <xplan:dientZurDarstellungVon xlink:href="#GML_51e17233-d921-46cb-83b9-af28451186a1" />
      <xplan:position>
        <gml:Point srsName="EPSG:25832" gml:id="GML_27888432-2c29-41c0-b6bc-d857207dced4">
          <gml:pos>565043.676 5940476.202</gml:pos>
        </gml:Point>
      </xplan:position>
      <xplan:drehwinkel uom="grad">0.0</xplan:drehwinkel>
      <xplan:skalierung>1.0</xplan:skalierung>
    </xplan:XP_PPO>
  </gml:featureMember>
</xplan:XPlanAuszug>