# Complete list of Bosnian cities and municipalities (143+ municipalities)
# Organized by entity and canton for reference
BOSNIAN_CITIES = [
    # =============================================
    # FEDERATION OF BOSNIA AND HERZEGOVINA (FBiH)
    # =============================================

    # Una-Sana Canton (8 municipalities)
    "Bihać",
    "Bosanska Krupa",
    "Bosanski Petrovac",
    "Bužim",
    "Cazin",
    "Ključ",
    "Sanski Most",
    "Velika Kladuša",

    # Posavina Canton (3 municipalities)
    "Domaljevac-Šamac",
    "Odžak",
    "Orašje",

    # Tuzla Canton (13 municipalities)
    "Banovići",
    "Čelić",
    "Doboj Istok",
    "Gračanica",
    "Gradačac",
    "Kalesija",
    "Kladanj",
    "Lukavac",
    "Sapna",
    "Srebrenik",
    "Teočak",
    "Tuzla",
    "Živinice",

    # Zenica-Doboj Canton (12 municipalities)
    "Breza",
    "Doboj Jug",
    "Kakanj",
    "Maglaj",
    "Olovo",
    "Tešanj",
    "Usora",
    "Vareš",
    "Visoko",
    "Zavidovići",
    "Zenica",
    "Žepče",

    # Bosnian-Podrinje Canton Goražde (3 municipalities)
    "Foča-Ustikolina",
    "Goražde",
    "Pale-Prača",

    # Central Bosnia Canton (12 municipalities)
    "Bugojno",
    "Busovača",
    "Dobretići",
    "Donji Vakuf",
    "Fojnica",
    "Gornji Vakuf-Uskoplje",
    "Jajce",
    "Kiseljak",
    "Kreševo",
    "Novi Travnik",
    "Travnik",
    "Vitez",

    # Herzegovina-Neretva Canton (9 municipalities)
    "Čapljina",
    "Čitluk",
    "Jablanica",
    "Konjic",
    "Mostar",
    "Neum",
    "Prozor-Rama",
    "Ravno",
    "Stolac",

    # West Herzegovina Canton (4 municipalities)
    "Grude",
    "Ljubuški",
    "Posušje",
    "Široki Brijeg",

    # Sarajevo Canton (9 municipalities)
    "Centar Sarajevo",
    "Hadžići",
    "Ilidža",
    "Ilijaš",
    "Novi Grad Sarajevo",
    "Novo Sarajevo",
    "Stari Grad Sarajevo",
    "Trnovo",
    "Vogošća",

    # Canton 10 / Livno Canton (6 municipalities)
    "Bosansko Grahovo",
    "Drvar",
    "Glamoč",
    "Kupres",
    "Livno",
    "Tomislavgrad",

    # =============================================
    # REPUBLIKA SRPSKA (64 municipalities)
    # =============================================

    # Banja Luka region
    "Banja Luka",
    "Čelinac",
    "Gradiška",
    "Jezero",
    "Kneževo",
    "Kotor Varoš",
    "Laktaši",
    "Mrkonjić Grad",
    "Prnjavor",
    "Ribnik",
    "Srbac",
    "Šipovo",

    # Doboj region
    "Brod",
    "Derventa",
    "Doboj",
    "Modriča",
    "Petrovo",
    "Stanari",
    "Šamac",
    "Teslić",
    "Vukosavlje",

    # Bijeljina region
    "Bijeljina",
    "Donji Žabar",
    "Lopare",
    "Pelagićevo",
    "Ugljevik",

    # Prijedor region
    "Kostajnica",
    "Kozarska Dubica",
    "Krupa na Uni",
    "Novi Grad",
    "Oštra Luka",
    "Prijedor",

    # Trebinje region
    "Berkovići",
    "Bileća",
    "Gacko",
    "Ljubinje",
    "Nevesinje",
    "Trebinje",

    # East Sarajevo region
    "Istočna Ilidža",
    "Istočni Stari Grad",
    "Istočno Novo Sarajevo",
    "Pale",
    "Sokolac",
    "Trnovo RS",

    # Foča region
    "Čajniče",
    "Foča",
    "Kalinovik",
    "Novo Goražde",
    "Rudo",

    # Višegrad region
    "Rogatica",
    "Višegrad",

    # Zvornik region
    "Bratunac",
    "Han Pijesak",
    "Milići",
    "Osmaci",
    "Srebrenica",
    "Šekovići",
    "Vlasenica",
    "Zvornik",

    # Other RS municipalities
    "Istočni Drvar",
    "Istočni Mostar",
    "Kupres RS",
    "Petrovac",

    # =============================================
    # BRČKO DISTRICT
    # =============================================
    "Brčko",

    # =============================================
    # ALTERNATE NAMES (for search/migration compatibility)
    # =============================================
    "Sarajevo",  # General Sarajevo reference
    "Bosanska Dubica",  # Old name for Kozarska Dubica
    "Bosanska Gradiška",  # Old name for Gradiška
    "Ustikolina",  # Part of Foča-Ustikolina
    "Ustiprača",  # Settlement in Goražde area
]

# Remove duplicates and sort alphabetically
BOSNIAN_CITIES = sorted(list(set(BOSNIAN_CITIES)))
