# -*- coding: utf-8 -*-
"""Static lookup tables for Vedic astrology calculations."""

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
         "Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury","Venus","Mars",
              "Jupiter","Saturn","Saturn","Jupiter"]

PLANETS7 = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
PLANETS9 = PLANETS7 + ["Rahu","Ketu"]

NAKSHATRAS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula",
    "Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"]

# Vimshottari lords repeat in this order starting from Ashwini
NAK_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]*3
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,"Rahu":18,
               "Jupiter":16,"Saturn":19,"Mercury":17}
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]

# --- Avakahada -------------------------------------------------------------
# Varna by Moon sign (index 0=Aries)
VARNA = ["Kshatriya","Vaishya","Shudra","Brahmin","Kshatriya","Vaishya",
         "Shudra","Brahmin","Kshatriya","Vaishya","Shudra","Brahmin"]

VASHYA = ["Chatushpada","Chatushpada","Manava","Jalachara","Vanachara","Manava",
          "Manava","Keeta","Manava","Jalachara","Manava","Jalachara"]
# (Sagittarius: first half Manava / second Chatushpada; Capricorn first half
#  Chatushpada / second Jalachara — handled in code by degree.)

# Yoni: (animal, gender) per nakshatra
YONI = [("Ashwa (Horse)","M"),("Gaja (Elephant)","M"),("Mesha (Sheep)","F"),
        ("Sarpa (Serpent)","M"),("Sarpa (Serpent)","F"),("Shwan (Dog)","F"),
        ("Marjara (Cat)","F"),("Mesha (Sheep)","M"),("Marjara (Cat)","M"),
        ("Mushaka (Rat)","M"),("Mushaka (Rat)","F"),("Gau (Cow)","M"),
        ("Mahisha (Buffalo)","F"),("Vyaghra (Tiger)","F"),("Mahisha (Buffalo)","M"),
        ("Vyaghra (Tiger)","M"),("Mriga (Deer)","F"),("Mriga (Deer)","M"),
        ("Shwan (Dog)","M"),("Vanara (Monkey)","M"),("Nakula (Mongoose)","M"),
        ("Vanara (Monkey)","F"),("Simha (Lion)","F"),("Ashwa (Horse)","F"),
        ("Simha (Lion)","M"),("Gau (Cow)","F"),("Gaja (Elephant)","F")]

GANA = ["Deva","Manushya","Rakshasa","Manushya","Deva","Manushya","Deva","Deva",
        "Rakshasa","Rakshasa","Manushya","Manushya","Deva","Rakshasa","Deva",
        "Rakshasa","Deva","Rakshasa","Rakshasa","Manushya","Manushya","Deva",
        "Rakshasa","Rakshasa","Manushya","Manushya","Deva"]

NADI = ["Adi","Madhya","Antya","Antya","Madhya","Adi","Adi","Madhya","Antya",
        "Antya","Madhya","Adi","Adi","Madhya","Antya","Antya","Madhya","Adi",
        "Adi","Madhya","Antya","Antya","Madhya","Adi","Adi","Madhya","Antya"]

# Naming syllables, 4 per nakshatra (pada 1..4)
SYLLABLES = [
 ["Chu","Che","Cho","La"],["Li","Lu","Le","Lo"],["A","I","U","E"],
 ["O","Va","Vi","Vu"],["Ve","Vo","Ka","Ki"],["Ku","Gha","Nga","Chha"],
 ["Ke","Ko","Ha","Hi"],["Hu","He","Ho","Da"],["Di","Du","De","Do"],
 ["Ma","Mi","Mu","Me"],["Mo","Ta","Ti","Tu"],["Te","To","Pa","Pi"],
 ["Pu","Sha","Na","Tha"],["Pe","Po","Ra","Ri"],["Ru","Re","Ro","Ta"],
 ["Ti","Tu","Te","To"],["Na","Ni","Nu","Ne"],["No","Ya","Yi","Yu"],
 ["Ye","Yo","Bha","Bhi"],["Bhu","Dha","Pha","Dha"],["Bhe","Bho","Ja","Ji"],
 ["Ju","Je","Jo","Gha"],["Ga","Gi","Gu","Ge"],["Go","Sa","Si","Su"],
 ["Se","So","Da","Di"],["Du","Tha","Jha","Na"],["De","Do","Cha","Chi"]]

TITHIS = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi",
          "Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi",
          "Trayodashi","Chaturdashi"]  # 15th handled as Purnima/Amavasya

YOGAS = ["Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda",
    "Sukarma","Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana",
    "Vajra","Siddhi","Vyatipata","Variyan","Parigha","Shiva","Siddha","Sadhya",
    "Shubha","Shukla","Brahma","Indra","Vaidhriti"]

KARANAS_MOVABLE = ["Bava","Balava","Kaulava","Taitila","Gara","Vanija","Vishti"]
KARANAS_FIXED = ["Shakuni","Chatushpada","Naga","Kimstughna"]

WEEKDAY_LORDS = {"Sunday":"Sun","Monday":"Moon","Tuesday":"Mars","Wednesday":"Mercury",
                 "Thursday":"Jupiter","Friday":"Venus","Saturday":"Saturn"}

TATVA = ["Agni (Fire)","Prithvi (Earth)","Vayu (Air)","Jala (Water)"]*3  # by sign

# --- Dignities -------------------------------------------------------------
EXALT = {"Sun":(0,10),"Moon":(1,3),"Mars":(9,28),"Mercury":(5,15),
         "Jupiter":(3,5),"Venus":(11,27),"Saturn":(6,20),
         "Rahu":(1,20),"Ketu":(7,20)}
DEBIL = {p:((s+6)%12,d) for p,(s,d) in EXALT.items()}
MOOLATRIKONA = {"Sun":(4,0,20),"Moon":(1,4,30),"Mars":(0,0,12),"Mercury":(5,16,20),
                "Jupiter":(8,0,10),"Venus":(6,0,15),"Saturn":(10,0,20)}
OWN_SIGNS = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],"Jupiter":[8,11],
             "Venus":[1,6],"Saturn":[9,10],"Rahu":[10],"Ketu":[7]}

# Natural friendships (BPHS)
FRIENDS = {"Sun":["Moon","Mars","Jupiter"],"Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"],"Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"],"Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"]}
ENEMIES = {"Sun":["Venus","Saturn"],"Moon":[],"Mars":["Mercury"],
    "Mercury":["Moon"],"Jupiter":["Mercury","Venus"],"Venus":["Sun","Moon"],
    "Saturn":["Sun","Moon","Mars"]}

# --- Special aspects (user-specified Drishti rules) ------------------------
DRISHTI = {"Sun":[7],"Moon":[7],"Mercury":[7],"Venus":[7],
           "Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10],
           "Rahu":[5,7,9],"Ketu":[5,7,9]}

# --- Shadbala constants ----------------------------------------------------
NAISARGIKA = {"Sun":60.0,"Moon":51.43,"Venus":42.85,"Jupiter":34.28,
              "Mercury":25.70,"Mars":17.14,"Saturn":8.57}
REQUIRED_VIRUPA = {"Sun":390,"Moon":360,"Mars":300,"Mercury":420,
                   "Jupiter":390,"Venus":330,"Saturn":300}

# --- Ashtakavarga benefic-point tables -------------------------------------
# For each planet's BAV: contributor -> list of houses (from contributor)
# that receive a bindu. "Lagna" is the ascendant. Totals: Sun 48, Moon 49,
# Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39; SAV = 337.
BAV = {
 "Sun":{"Sun":[1,2,4,7,8,9,10,11],"Moon":[3,6,10,11],"Mars":[1,2,4,7,8,9,10,11],
   "Mercury":[3,5,6,9,10,11,12],"Jupiter":[5,6,9,11],"Venus":[6,7,12],
   "Saturn":[1,2,4,7,8,9,10,11],"Lagna":[3,4,6,10,11,12]},
 "Moon":{"Sun":[3,6,7,8,10,11],"Moon":[1,3,6,7,10,11],"Mars":[2,3,5,6,9,10,11],
   "Mercury":[1,3,4,5,7,8,10,11],"Jupiter":[1,4,7,8,10,11,12],
   "Venus":[3,4,5,7,9,10,11],"Saturn":[3,5,6,11],"Lagna":[3,6,10,11]},
 "Mars":{"Sun":[3,5,6,10,11],"Moon":[3,6,11],"Mars":[1,2,4,7,8,10,11],
   "Mercury":[3,5,6,11],"Jupiter":[6,10,11,12],"Venus":[6,8,11,12],
   "Saturn":[1,4,7,8,9,10,11],"Lagna":[1,3,6,10,11]},
 "Mercury":{"Sun":[5,6,9,11,12],"Moon":[2,4,6,8,10,11],"Mars":[1,2,4,7,8,9,10,11],
   "Mercury":[1,3,5,6,9,10,11,12],"Jupiter":[6,8,11,12],
   "Venus":[1,2,3,4,5,8,9,11],"Saturn":[1,2,4,7,8,9,10,11],
   "Lagna":[1,2,4,6,8,10,11]},
 "Jupiter":{"Sun":[1,2,3,4,7,8,9,10,11],"Moon":[2,5,7,9,11],
   "Mars":[1,2,4,7,8,10,11],"Mercury":[1,2,4,5,6,9,10,11],
   "Jupiter":[1,2,3,4,7,8,10,11],"Venus":[2,5,6,9,10,11],"Saturn":[3,5,6,12],
   "Lagna":[1,2,4,5,6,7,9,10,11]},
 "Venus":{"Sun":[8,11,12],"Moon":[1,2,3,4,5,8,9,11,12],"Mars":[3,5,6,9,11,12],
   "Mercury":[3,5,6,9,11],"Jupiter":[5,8,9,10,11],
   "Venus":[1,2,3,4,5,8,9,10,11],"Saturn":[3,4,5,8,9,10,11],
   "Lagna":[1,2,3,4,5,8,9,11]},
 "Saturn":{"Sun":[1,2,4,7,8,10,11],"Moon":[3,6,11],"Mars":[3,5,6,10,11,12],
   "Mercury":[6,8,9,10,11,12],"Jupiter":[5,6,11,12],"Venus":[6,11,12],
   "Saturn":[3,5,6,11],"Lagna":[1,3,4,6,10,11]},
}

# Indu Lagna kalas
INDU_KALA = {"Sun":30,"Moon":16,"Mars":6,"Mercury":8,"Jupiter":10,"Venus":12,"Saturn":1}

# Chara Karaka names (7-karaka scheme)
KARAKA_NAMES = ["Atmakaraka (AK)","Amatyakaraka (AmK)","Bhratrikaraka (BK)",
    "Matrikaraka (MK)","Putrakaraka (PK)","Gnatikaraka (GK)","Darakaraka (DK)"]

# Numerology letter values
CHALDEAN = {**{c:1 for c in "AIJQY"},**{c:2 for c in "BKR"},**{c:3 for c in "CGLS"},
            **{c:4 for c in "DMT"},**{c:5 for c in "EHNX"},**{c:6 for c in "UVW"},
            **{c:7 for c in "OZ"},**{c:8 for c in "FP"}}
PYTHAGOREAN = {c:(i%9)+1 for i,c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
