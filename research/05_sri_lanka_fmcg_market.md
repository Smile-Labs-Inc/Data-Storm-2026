# TL;DR

- The likely data-owner context is strong: Elephant House is the beverage brand of Ceylon Cold Stores PLC, and Ceylon Cold Stores is a John Keells Group company active in Sri Lankan carbonated soft drinks and frozen confectionery.
- Sri Lanka beverage demand should be modeled as both demand and constraint: province, outlet type, tourist flow, calendar spikes, route frequency, credit, cooler access, and dry-day restrictions all matter.
- The strongest feature lift is likely from local interactions: outlet channel x province, April/December seasonality x channel, tourist zone x month, and historical sales x constraint proxies.

# Domain Background

## John Keells / Elephant House / Ceylon Cold Stores

The competition host, John Keells Group, is directly relevant to the beverage market. Ceylon Cold Stores PLC describes itself as a John Keells Group company and the operator of the Elephant House brand, with roots in the Colombo Ice Company and a current business in beverages and frozen confectionery. Its public company materials also describe Ceylon Cold Stores as a major Sri Lankan food and beverage manufacturer. Sources: [Elephant House corporate profile](https://www.elephanthouse.lk/corporate), [Ceylon Cold Stores annual reports](https://www.elephanthouse.lk/media-hub/financial-reports/annual-reports/), [Ceylon Cold Stores Annual Report 2023/24 PDF](https://www.elephanthouse.lk/annual-reports/annual-report-2023-24.pdf).

This makes Elephant House / Ceylon Cold Stores a plausible data source or at least a close market analogue for the hackathon problem. The target is latent monthly maximum outlet volume, which matches how a beverage manufacturer or distributor would think about outlet potential, not just observed sell-in.

## Top Beverage Brands And Market Structure

The carbonated soft drink market is led by large national and multinational players. Public market reporting names Coca-Cola, Elephant House / KiK Cola, and Pepsi as the major cola and soft-drink competitors in Sri Lanka. A Sunday Times business article from 2011 reported Coca-Cola and Elephant House at roughly 42-43% each, Pepsi at about 10%, and smaller brands such as Sha Cola and My Cola making up the rest. This is old data, so use it as structure, not current truth. Source: [Sunday Times, "Battle of the Colas"](https://sundaytimes.lk/110116/BusinessTimes/bt01.html).

More recent market summaries still place Coca-Cola Beverages Sri Lanka among the leading soft-drink companies, while Elephant House remains a major local brand with broad island-wide distribution. Sources: [Euromonitor Soft Drinks in Sri Lanka](https://www.euromonitor.com/soft-drinks-in-sri-lanka/report), [Elephant House beverages](https://www.elephanthouse.lk/beverages/elephant-house-soft-drinks/), [Elephant House corporate profile](https://www.elephanthouse.lk/corporate).

Urban and rural demand should not be treated the same. Modern grocery has grown, but Sri Lanka still has low modern trade penetration compared with regional peers. Fitch-linked reporting put supermarket penetration around 12-15% of FMCG sales, while traditional trade remains the dominant channel. Source: [EconomyNext on Sri Lanka supermarkets and Fitch](https://economynext.com/sri-lanka-supermarkets-to-grow-price-controls-regulations-a-threat-fitch-8724/), [Oxford Business Group retail overview](https://oxfordbusinessgroup.com/reports/sri-lanka/2019-report/economy/expanding-the-base-large-urban-shopping-centres-and-e-commerce-find-opportunity-while-rural-inroads-are-also-set-to-expand).

## Trade Channel Structure

Sri Lanka is a mixed traditional-trade and modern-trade market.

- Kade / corner shop: high-frequency, convenience-led purchase point. Main drivers are nearby households, school/work footfall, credit with distributor, pack availability, chilled stock, and impulse purchases.
- Supermarket / "smukai" in the prompt: modern trade led by chains such as Cargills Food City, Keells, and Arpico. Main drivers are basket size, promotions, household stocking, urban income, parking/access, and cold-chain quality. Sources: [EconomyNext on supermarket players](https://economynext.com/sri-lanka-supermarkets-to-grow-price-controls-regulations-a-threat-fitch-8724/), [Oxford Business Group retail overview](https://oxfordbusinessgroup.com/reports/sri-lanka/2019-report/economy/expanding-the-base-large-urban-shopping-centres-and-e-commerce-find-opportunity-while-rural-inroads-are-also-set-to-expand).
- Eatery / restaurant: immediate-consumption channel. Main drivers are meal traffic, lunch/dinner peaks, tourist traffic, menu pairing, and chilled single-serve availability.
- Hotel: tourist and event-driven. Main drivers are occupancy, domestic holiday travel, foreign tourist season, weddings, cricket tours, and premium pack mix.
- Kiosk / roadside stall: transit and heat-driven. Main drivers are bus stands, railway stations, schools, markets, temples, beaches, and roadside footfall.
- Pharmacy: lower beverage baseline, but can sell water, isotonic drinks, juices, and impulse chilled drinks. Main drivers are urban density, clinic/hospital adjacency, and hot-weather hydration.
- Bakery: strong snack-pairing channel. Main drivers are morning/evening bakery traffic, school/work commuters, tea-time demand, and single-serve cold drink availability.

## Province-Level Economic Context

Western Province is the highest-potential base market. It includes Colombo and the largest urban consumer base, with the strongest services and industry concentration. Central Bank / news reporting on provincial GDP shows Western Province as the largest contributor to nominal GDP, with over 40% of GDP in recent reporting. Sources: [CBSL Provincial GDP](https://www.cbsl.gov.lk/en/pgdp-2022), [Newswire on 2024 provincial GDP](https://www.newswire.lk/2025/12/22/western-province-maintains-lead-in-2024-provincial-gdp-data/), [CBSL Socio Economic Data 2025 PDF](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/otherpub/publication_sri_lanka_socio_economic_data_folder_2025_e.pdf).

Demand implication: Colombo and nearby Western Province outlets should get a higher base potential, stronger modern trade signal, stronger eating-out signal, and higher premium-pack potential. Observed sales below peer outlets may mean constraint, not weak demand.

Central Province includes Kandy and tea-estate / hill-country areas. It has a mix of religious tourism, local urban centers, estate-worker communities, and cooler climate. Sources for provincial contribution and tourism context: [CBSL Socio Economic Data 2025 PDF](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/otherpub/publication_sri_lanka_socio_economic_data_folder_2025_e.pdf), [Blue Lanka Tours on December high season and Kandy](https://www.bluelankatours.com/blog/sri-lanka-in-december-what-to-expect-as-the-high-season-begins).

Demand implication: Kandy and tourist corridors can spike with pilgrimage and tourist travel, while estate areas may have lower purchasing power but stable small-pack demand.

North-Western Province includes Kurunegala and has a strong agriculture role. Recent provincial GDP reporting names North Western as a leading contributor outside Western Province and a major agriculture contributor. Sources: [Newswire on provincial GDP](https://www.newswire.lk/2025/12/22/western-province-maintains-lead-in-2024-provincial-gdp-data/), [CBSL Socio Economic Data 2025 PDF](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/otherpub/publication_sri_lanka_socio_economic_data_folder_2025_e.pdf).

Demand implication: rural and semi-urban kades, market towns, and transport routes matter. Agriculture income cycles and heat exposure may support bottled water and value soft drinks.

Southern Province includes Galle and coastal tourism / fishing areas. Tourism sources describe the south and southwest coasts, including Galle and Mirissa, as high-season destinations in December-March. Source: [Blue Lanka Tours on December high season](https://www.bluelankatours.com/blog/sri-lanka-in-december-what-to-expect-as-the-high-season-begins), [Alike Sri Lanka season guide](https://alike.io/blog/best-time-to-visit-sri-lanka).

Demand implication: beach, hotel, restaurant, and transit outlets can outperform normal population-based expectations during tourist months. Fishing and port-linked areas may also have early-morning trade and hydration demand.

## 2024-2025 Macro Context

Sri Lanka moved from the 2022 crisis into a clearer recovery phase in 2024-2025. The IMF reported stronger growth, lower inflation, stronger reserves, and continued reform progress under the Extended Fund Facility. The World Bank's 2025 update also describes recovery, currency appreciation from the crisis period, lower inflation, and improving reserves. Sources: [IMF April 2025 staff visit](https://www.imf.org/en/News/Articles/2025/04/11/pr25102-srilanka-imf-staff-team-concludes-visit), [World Bank Sri Lanka Development Update 2025](https://www.worldbank.org/en/country/srilanka/publication/sri-lanka-development-update-2025).

Retail implication: 2024 and 2025 observed sales may be distorted by recovery, not stable long-run demand. Fuel availability, fewer import constraints, lower inflation, and normalizing credit can raise observed sales toward true demand. A model trained on constrained history should avoid treating 2022-2023 lows as permanent outlet weakness.

# Seasonality Drivers

## April: Sinhala and Tamil New Year

Sinhala and Tamil New Year falls in mid-April and is one of Sri Lanka's biggest household and retail seasons. Public holiday calendars list April 13-14 as the New Year period in 2026. Source: [Timeanddate Sri Lanka holidays 2026](https://www.timeanddate.com/holidays/sri-lanka/2026), [PublicHolidays.lk](https://publicholidays.lk/).

Feature implication: April should carry a strong positive demand prior, especially for supermarkets, kades, bakeries, eateries, and outlets near bus/rail routes. But 2025 reporting also warns that consumers remained price-sensitive during the festive period, so income and price proxies should interact with the April flag. Source: [Sunday Times on 2025 festive spending restraint](https://www.sundaytimes.lk/250413/news/festive-time-is-spending-time-but-with-restraint-594670.html).

## December: Christmas And Tourist Peak

December combines Christmas, domestic travel, and the start of the main tourism high season for the west/south coast and many central destinations. Public calendars list Christmas on December 25, and travel sources describe December-March as the main high season for many Sri Lankan routes. Sources: [Timeanddate Sri Lanka holidays 2026](https://www.timeanddate.com/holidays/sri-lanka/2026), [Blue Lanka Tours December high season](https://www.bluelankatours.com/blog/sri-lanka-in-december-what-to-expect-as-the-high-season-begins), [Alike Sri Lanka season guide](https://alike.io/blog/best-time-to-visit-sri-lanka).

Feature implication: December should boost hotels, eateries, bakeries, supermarkets, tourist-zone kades, beach kiosks, and Colombo entertainment areas.

## Poya Days

Poya days are monthly full-moon public holidays in Sri Lanka. Alcohol sales are restricted on Poya days and other official dry days, with limited hotel exemptions in some cases. Sources: [PublicHolidays.lk Poya Day](https://publicholidays.lk/poya-day/), [Poya Wikipedia](https://en.wikipedia.org/wiki/Poya), [The Morning on Excise closure days](https://www.themorning.lk/articles/YOrNju4xQh4IQwZc7LM4).

Feature implication: Poya can reduce alcohol-adjacent traffic while raising family, temple, pilgrimage, and non-alcoholic beverage traffic. The sign may differ by outlet type: hotel bars lose some sales, but temple-area kiosks and family eateries may gain soft-drink demand.

## Ramadan / Eid

Sri Lankan holiday calendars include Eid al-Fitr and Eid al-Adha as public holidays. In 2026, public calendars place Ramadan beginning in February and Eid al-Fitr in March. Source: [Timeanddate Sri Lanka holidays 2026](https://www.timeanddate.com/holidays/sri-lanka/2026).

Feature implication: use Muslim-population or district proxies if available. Expect evening-heavy food and drink demand during Ramadan and celebration demand around Eid, especially in relevant neighborhoods.

## Vesak

Vesak is a major Buddhist holiday around May and appears in Sri Lankan public calendars as Vesak Full Moon Poya and the following day. Source: [Timeanddate Sri Lanka holidays 2026](https://www.timeanddate.com/holidays/sri-lanka/2026), [PublicHolidays.lk](https://publicholidays.lk/).

Feature implication: outlet demand near temples, lantern zones, city centers, and pilgrimage routes may rise. Alcohol-adjacent channels may weaken due to dry-day rules.

## Deepavali

Deepavali is listed as a public holiday in Sri Lanka, with 2026 calendars placing it in November. Source: [Timeanddate Sri Lanka holidays 2026](https://www.timeanddate.com/holidays/sri-lanka/2026), [PublicHolidays.lk](https://publicholidays.lk/).

Feature implication: use Tamil/Hindu population or district proxies where possible. Demand can rise in Northern, Eastern, Central estate, and urban Tamil communities.

## Cricket Season And Match Days

Cricket can produce sharp local demand shocks. Reporting on major cricket events in Sri Lanka describes spikes in tourist arrivals, hotel prices, restaurant/bar traffic, and Colombo entertainment demand around high-profile matches. Sources: [Reuters via Today on India-Pakistan cricket tourism](http://today.reuters.com/sports/cricket/india-pakistan-fans-flock-colombo-windfall-tourism-2026-02-13/), [The Hindu on Sri Lanka tourism and cricket](https://www.thehindu.com/sport/cricket/india-vs-pakistan-sun-shines-on-lanka-tourism-economy/article70634821.ece), [Travel Talk Asia on tourism growth](https://www.traveltalkasia.com/2026/02/20/sri-lanka-tourism-accelerates-growth-through-strategic-investments-and-new-initiatives/).

Feature implication: add cricket-match windows if schedule data can be sourced. Strongest effect should be near stadiums, hotels, bars, restaurants, transit hubs, and Colombo tourist zones.

# Constraint Patterns

## Credit Cycles

Traditional retailers often buy on distributor or wholesaler credit. Exact outlet-level terms are not public in the sources found, but Sri Lankan supermarket/manufacturer reporting shows formal trade payment terms can be long, with 45-60 day terms and extensions cited for supermarkets. Source: [Sunday Times on supermarket supplier terms](https://sundaytimes.lk/110306/BusinessTimes/bt13.html).

Model implication: low observed monthly sales can mean credit exhaustion or delayed repayment, not low latent demand. If the data has last purchase date, invoice amount, credit limit, overdue balance, or payment behavior, these are constraint features.

## Distributor Delivery Routes

Elephant House reports broad distribution across Sri Lanka, and KiK Cola reached tens of thousands of retail outlets soon after launch in older reporting. Sources: [Elephant House beverages](https://www.elephanthouse.lk/beverages/elephant-house-soft-drinks/), [Sunday Times, "Battle of the Colas"](https://sundaytimes.lk/110116/BusinessTimes/bt01.html).

The user-provided domain assumption says distributor delivery is typically 1-3 times per week per outlet. Treat this as a practical hypothesis unless the dataset includes actual visit frequency. It matters because observed sales are capped by route frequency, case drop size, and stockout duration.

Model implication: a high-demand outlet with weekly delivery can look smaller than a lower-demand outlet with three visits per week. Route-day and distance-to-depot proxies can help separate true demand from supply.

## Cooler Placement And Cold Availability

Cold availability is central to immediate-consumption soft drinks. Public reporting confirms major beverage firms compete through brand investment, bottles, crates, plant equipment, and distribution capacity; public sources do not give outlet-level cooler contracts. Source: [Sunday Times, "Battle of the Colas"](https://sundaytimes.lk/110116/BusinessTimes/bt01.html).

Model implication: cooler presence, cooler size, competitor cooler, electricity reliability, and outlet type should be treated as supply-side caps. For kades, kiosks, bakeries, eateries, and transit points, no cooler can suppress observed sales below potential.

## Election-Period Restrictions

Sri Lanka can impose alcohol retail restrictions around elections. During the 2024 presidential election weekend, reporting said liquor shops and wine stores were closed island-wide, with limited hotel exemptions. Sources: [Newswire election liquor closure](https://www.newswire.lk/2024/09/14/all-liquor-shops-to-close-during-election-weekend/), [TimesOnline election liquor closure](https://sundaytimes.lk/online/news-online/Liquor-shops-to-close-in-view-of-Presidential-Election/2-1146850), [The Morning election restrictions](https://www.themorning.lk/articles/QiuNNSA37N2q5RDNVbWf).

Model implication: election months can alter outlet traffic and beverage mix. Alcohol restrictions may shift demand to non-alcoholic beverages in some channels but reduce nightlife footfall in others.

## Fuel, FX, And Import Constraints

The 2022 crisis created fuel and import disruption, while 2024-2025 reports show recovery, stronger reserves, lower inflation, and more normal activity. Sources: [IMF April 2025 staff visit](https://www.imf.org/en/News/Articles/2025/04/11/pr25102-srilanka-imf-staff-team-concludes-visit), [World Bank Sri Lanka Development Update 2025](https://www.worldbank.org/en/country/srilanka/publication/sri-lanka-development-update-2025), [CBSL Annual Economic Review 2024 PDF](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/aer/2024/en/06_Chapter_01.pdf).

Model implication: older observed volume can reflect disrupted delivery, not weak outlet potential. Add year/month recovery features if history spans the crisis and recovery period.

# 10 Domain-Driven Feature Ideas

1. `province_channel_base_potential`: target-encoded or smoothed historical sales by province x outlet channel. This captures Western supermarket potential, Southern tourism outlets, Central pilgrimage/tourism outlets, and North-Western rural trade.

2. `april_avurudu_uplift`: April flag interacted with outlet channel, district income proxy, and historical small-pack share. Strongest expected channels: kade, supermarket, bakery, eatery, transit kiosk.

3. `december_tourism_peak_score`: December/January flag multiplied by tourist-zone proxy, hotel/eatery/kiosk channel, and Southern/Western/Central province flags.

4. `poya_dry_day_exposure`: count of Poya/dry days in the month x outlet type. Use separate signs for temple/pilgrimage zones, hotels/bars, family eateries, and ordinary kades.

5. `religious_festival_locality_score`: month flags for Vesak, Ramadan/Eid, Deepavali, and Christmas interacted with district religion/ethnicity proxies if available. This avoids applying one national uplift everywhere.

6. `cricket_event_proximity_window`: match-day or tournament-month flag x distance to stadium/city center/hotel cluster. If no stadium coordinates exist, use Colombo/Kandy/Galle city proxy plus month.

7. `route_supply_constraint_index`: delivery frequency, days since last delivery, distance to distributor/depot, average drop size, and stockout history. This is a direct proxy for observed sales being capped below latent demand.

8. `credit_binding_risk`: overdue balance, credit limit utilization, average days to pay, missed invoices, or low order after high prior demand. This flags outlets that could sell more but cannot buy more.

9. `cold_availability_multiplier`: cooler ownership/presence/size, electricity reliability, channel, and competitor cooler proxy. This should matter most for immediate-consumption outlets.

10. `macro_recovery_adjusted_trend`: time trend from 2022-2025 with inflation/fuel/FX recovery proxies, interacted with province and channel. This prevents the model from underestimating January 2026 potential based on crisis-era suppressed sales.

# References

- Ceylon Cold Stores / Elephant House corporate profile: https://www.elephanthouse.lk/corporate
- Ceylon Cold Stores annual reports: https://www.elephanthouse.lk/media-hub/financial-reports/annual-reports/
- Ceylon Cold Stores Annual Report 2023/24 PDF: https://www.elephanthouse.lk/annual-reports/annual-report-2023-24.pdf
- Elephant House beverages: https://www.elephanthouse.lk/beverages/elephant-house-soft-drinks/
- Sunday Times, "Battle of the Colas": https://sundaytimes.lk/110116/BusinessTimes/bt01.html
- Euromonitor, Soft Drinks in Sri Lanka: https://www.euromonitor.com/soft-drinks-in-sri-lanka/report
- EconomyNext, Sri Lanka supermarkets and Fitch: https://economynext.com/sri-lanka-supermarkets-to-grow-price-controls-regulations-a-threat-fitch-8724/
- Oxford Business Group, Sri Lanka retail overview: https://oxfordbusinessgroup.com/reports/sri-lanka/2019-report/economy/expanding-the-base-large-urban-shopping-centres-and-e-commerce-find-opportunity-while-rural-inroads-are-also-set-to-expand
- Sunday Times, supermarket supplier terms: https://sundaytimes.lk/110306/BusinessTimes/bt13.html
- CBSL Provincial GDP: https://www.cbsl.gov.lk/en/pgdp-2022
- CBSL Socio Economic Data 2025 PDF: https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/otherpub/publication_sri_lanka_socio_economic_data_folder_2025_e.pdf
- Newswire, 2024 provincial GDP: https://www.newswire.lk/2025/12/22/western-province-maintains-lead-in-2024-provincial-gdp-data/
- IMF Sri Lanka staff visit, April 2025: https://www.imf.org/en/News/Articles/2025/04/11/pr25102-srilanka-imf-staff-team-concludes-visit
- World Bank Sri Lanka Development Update 2025: https://www.worldbank.org/en/country/srilanka/publication/sri-lanka-development-update-2025
- CBSL Annual Economic Review 2024 PDF: https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/publications/aer/2024/en/06_Chapter_01.pdf
- Timeanddate Sri Lanka holidays 2026: https://www.timeanddate.com/holidays/sri-lanka/2026
- PublicHolidays.lk: https://publicholidays.lk/
- PublicHolidays.lk Poya Day: https://publicholidays.lk/poya-day/
- Wikipedia, Poya: https://en.wikipedia.org/wiki/Poya
- The Morning, Excise closure days: https://www.themorning.lk/articles/YOrNju4xQh4IQwZc7LM4
- Sunday Times, 2025 festive spending restraint: https://www.sundaytimes.lk/250413/news/festive-time-is-spending-time-but-with-restraint-594670.html
- Blue Lanka Tours, December high season: https://www.bluelankatours.com/blog/sri-lanka-in-december-what-to-expect-as-the-high-season-begins
- Alike, Sri Lanka season guide: https://alike.io/blog/best-time-to-visit-sri-lanka
- Reuters via Today, cricket tourism: http://today.reuters.com/sports/cricket/india-pakistan-fans-flock-colombo-windfall-tourism-2026-02-13/
- The Hindu, cricket and Sri Lanka tourism: https://www.thehindu.com/sport/cricket/india-vs-pakistan-sun-shines-on-lanka-tourism-economy/article70634821.ece
- Travel Talk Asia, tourism growth: https://www.traveltalkasia.com/2026/02/20/sri-lanka-tourism-accelerates-growth-through-strategic-investments-and-new-initiatives/
- Newswire, election liquor closure: https://www.newswire.lk/2024/09/14/all-liquor-shops-to-close-during-election-weekend/
- TimesOnline, election liquor closure: https://sundaytimes.lk/online/news-online/Liquor-shops-to-close-in-view-of-Presidential-Election/2-1146850
- The Morning, election restrictions: https://www.themorning.lk/articles/QiuNNSA37N2q5RDNVbWf
