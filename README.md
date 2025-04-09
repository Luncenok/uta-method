# Multi-Criteria Decision Analysis Report

## Authors
- Mateusz Stawicki 155900
- Mateusz Idziejczak 155842

## Car Selection Problem Analysis

### 1. Dataset Description

We analyzed a set of 10 small city cars available for sale within 100 km of Koziegłowy, with prices under 40,000 PLN. The data comes from [OTOMOTO](https://www.otomoto.pl/), where we scraped listings for cars that might suit a PUT student's needs. We narrowed down from 50 initial listings to 10 representative options to keep our analysis manageable.

Our *totally fictional* buyer is a student living in Koziegłowy, Wielkopolskie - who needs a reliable city car that balances cost, age, mileage, and performance. Since they're a student, practical considerations outweigh aesthetics or comfort - they want the best value for money and maybe a bit of engine power to impress friends.

Specifically, the dataset comprises the first 50 listings from [this exact url](https://www.otomoto.pl/osobowe/seg-mini/kozieglowy_8905?search%5Bdist%5D=100&search%5Bfilter_enum_fuel_type%5D=petrol&search%5Bfilter_float_price%3Ato%5D=40000&search%5Badvanced_search_expanded%5D=true)

Not all available scraped data was used for the MCDA in the end. Still, it is present in the dataset for reference.

#### Full dataset
|title|subtitle|price|currency|year|mileage_km|fuel_type|gearbox|location|seller_type|price_evaluation|url|engine_size_cm3|power_hp|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Renault Clio 0.9 Energy TCe Limited|898 cm3 - 90 KM - Salon Polska, Pierwszy właściciel, bezwypadkowy i bezkolizyjny|39500|PLN|2017|60098|Benzyna|Manualna|Rawicz (Wielkopolskie)|Prywatny sprzedawca|Powyżej średniej|https://www.otomoto.pl/osobowe/oferta/renault-clio-salon-polska-pierwszy-wlasciciel-bezwypadkowy-i-bezkolizyjny-ID6Hhjbk.html|898|90|
|Dacia Sandero Stepway TCe 90 (S&S) Essential|898 cm3 - 90 KM|39360|PLN|2019|65900|Benzyna|Manualna|Dobrcz (Kujawsko-pomorskie)|Prywatny sprzedawca|W granicach średniej|https://www.otomoto.pl/osobowe/oferta/dacia-sandero-stepway-ID6HhdIw.html|898|90|
...

#### MCDA dataset
|title|price &darr; <br>(4,700-39,500 PLN)|year &uarr; <br>(2000-2019)|mileage_km &darr; <br>(49,459-374,000 km)|engine_size_cm3 &uarr; <br>(875-1,798 cm³)|power_hp &uarr; <br>(60-160 HP)|
|---|---|---|---|---|---|
|Renault Clio 0.9 Energy TCe Limited|39500|2017|60098|898|90|
|Renault Megane 1.4 RN 16V|4700|2001|173117|1390|95|
|Dacia Sandero Stepway TCe 90 (S&S) Essential|39360|2019|65900|898|90|
|Mitsubishi Space Star|26000|2017|82000|1193|80|
|Nissan Micra|16500|2011|177491|1198|80|
|Ford KA|19300|2014|139990|1242|69|
|Alfa Romeo Mito 0.9 TwinAir Progression|7800|2009|232000|875|85|
|Fiat 500 1.2 8V Anniversario|13900|2012|93000|1242|69|
|Kia Picanto|36900|2018|56213|998|67|
|Audi A3|22500|2000|374000|1798|160|
...