"""
Procedural name generator for the Discord Motorsport Universe.
Generates realistic driver names by region with weighted nationality assignment.
"""
from __future__ import annotations
import random
from typing import Optional

# ─── First Names by Region ────────────────────────────────────────────────

FIRST_NAMES = {
    "europe_uk": [
        "James", "Oliver", "George", "Harry", "Jack", "Charlie", "Thomas",
        "Daniel", "Samuel", "William", "Alexander", "Henry", "Edward",
        "Max", "Leo", "Oscar", "Archie", "Theo"
    ],
    "europe_de": [
        "Finn", "Leon", "Lukas", "Maximilian", "Felix", "Jonas", "Niklas",
        "Luca", "Tim", "Lukas", "Elias", "Paul", "Julian", "Fabian",
        "Luis", "Noah", "Ben", "David", "Simon"
    ],
    "europe_fr": [
        "Lucas", "Hugo", "Louis", "Gabriel", "Raphaël", "Jules", "Adam",
        "Arthur", "Maël", "Léo", "Nathan", "Mathis", "Ethan", "Tom",
        "Théo", "Nolan", "Clément", "Antoine"
    ],
    "europe_it": [
        "Leonardo", "Lorenzo", "Francesco", "Alessandro", "Andrea", "Matteo",
        "Luca", "Gabriele", "Riccardo", "Tommaso", "Edoardo", "Marco",
        "Antonio", "Federico", "Giovanni", "Raffaele", "Daniele"
    ],
    "europe_es": [
        "Mateo", "Pablo", "Alejandro", "Daniel", "Leo", "Lucas", "Manuel",
        "Hugo", "Diego", "Javier", "Alvaro", "Carlos", "Miguel", "Sergio",
        "Jorge", "Raul", "Ivan", "Marcos"
    ],
    "europe_nl": [
        "Daan", "Sem", "Lucas", "Finn", "Levi", "Bram", "Jesse", "Thomas",
        "Tim", "Max", "Ruben", "Lars", "Sven", "Niels", "Wout", "Joost"
    ],
    "europe_nordic": [
        "Elias", "Oliver", "Liam", "William", "Noah", "Oscar", "Hugo",
        "Axel", "Erik", "Lars", "Anders", "Magnus", "Sven", "Björn",
        "Henrik", "Nils", "Olof", "Karl"
    ],
    "europe_east": [
        "Jakub", "Jan", "Tomas", "Piotr", "Mikhail", "Dmitri", "Andrei",
        "Ivan", "Nikolai", "Alexei", "Pavel", "Yuri", "Artem", "Sergei",
        "Krzysztof", "Marek", "Adam", "Mateusz"
    ],
    "south_america_br": [
        "Carlos", "Lucas", "Gabriel", "Rafael", "Felipe", "Bruno",
        "Thiago", "Vinicius", "Gustavo", "Paulo", "Eduardo", "Marcos",
        "Pedro", "Leonardo", "André", "Diego", "Luis", "Guilherme"
    ],
    "south_america_ar": [
        "Santiago", "Mateo", "Lautaro", "Bruno", "Franco", "Emiliano",
        "Joaquín", "Nicolás", "Luciano", "Alejandro", "Martín", "Juan",
        "Diego", "Valentino", "Federico", "Agustín"
    ],
    "south_america_co": [
        "Santiago", "Carlos", "Andrés", "Juan", "Miguel", "Pablo",
        "Daniel", "Sebastián", "Felipe", "Jorge", "Oscar", "Camilo",
        "Luis", "David", "Manuel"
    ],
    "north_america_us": [
        "Ethan", "Jackson", "Mason", "Luke", "Ryan", "Tyler", "Dylan",
        "Hunter", "Carson", "Landon", "Carter", "Logan", "Jake", "Cole",
        "Chase", "Connor", "Aaron", "Jason"
    ],
    "north_america_ca": [
        "Liam", "Noah", "Oliver", "Ethan", "Lucas", "Jack", "James",
        "Benjamin", "Logan", "Owen", "William", "Dylan", "Ryan", "Carter",
        "Nathan", "Connor", "Samuel"
    ],
    "north_america_mx": [
        "Santiago", "Mateo", "Diego", "Luis", "Carlos", "Miguel",
        "Alejandro", "Emiliano", "Juan", "Pablo", "Fernando", "Andrés",
        "Eduardo", "Ricardo", "Javier"
    ],
    "asia_jp": [
        "Kenji", "Hiroshi", "Takashi", "Yuki", "Sho", "Ryo", "Kenta",
        "Daiki", "Shin", "Kazuki", "Takeshi", "Ryota", "Koji", "Yuta",
        "Satoshi", "Taro", "Jun", "Ren"
    ],
    "asia_cn": [
        "Wei", "Chen", "Ming", "Hao", "Jun", "Yang", "Lei", "Kai",
        "Peng", "Tao", "Zhi", "Long", "Qiang", "Feng", "Bin", "Lin",
        "Xin", "Lei", "Dong"
    ],
    "asia_kr": [
        "Min-Jun", "Seo-Jun", "Ji-Ho", "Hyun-Woo", "Jae-Won", "Sang-Min",
        "Dong-Hyun", "Young-Jae", "Jin-Ho", "Tae-Yang", "Kwang-Soo",
        "Jung-Hwan", "Woo-Jin", "Han-Sol"
    ],
    "asia_in": [
        "Arjun", "Rohan", "Vikram", "Aryan", "Karan", "Dev", "Ravi",
        "Aditya", "Rahul", "Amit", "Siddharth", "Raj", "Aakash", "Kunal",
        "Vivek", "Manish", "Harsh", "Nikhil"
    ],
    "asia_se": [
        "Somchai", "Thanawat", "Anurak", "Kittipat", "Adisak", "Minh",
        "Tuan", "Phong", "Huy", "Duc", "Anh", "Budi", "Agus", "Hendra",
        "Dwi", "Rizky"
    ],
    "africa_za": [
        "Thabo", "Lungile", "Sipho", "Bongani", "Musa", "Sizwe",
        "Nkosi", "Mandla", "Jabulani", "Kagiso", "Tendai", "Dumisani",
        "Lwazi", "Vusumuzi"
    ],
    "africa_ng": [
        "Chidi", "Kofi", "Emeka", "Oluwaseun", "Chinedu", "Tunde",
        "Kwame", "Adebayo", "Femi", "Kehinde", "Tajudeen", "Obinna",
        "Chibueze", "Eze"
    ],
    "africa_ke": [
        "John", "David", "Peter", "James", "Joseph", "Daniel", "Samuel",
        "Patrick", "Stephen", "Michael", "Paul", "George", "Thomas"
    ],
    "africa_ma": [
        "Ahmed", "Mohammed", "Hassan", "Youssef", "Omar", "Ali", "Karim",
        "Rachid", "Soulaimane", "Amine", "Mehdi", "Hicham", "Sami"
    ],
    "oceania_au": [
        "Jack", "Oliver", "William", "James", "Thomas", "Liam", "Noah",
        "Ethan", "Lucas", "Harrison", "Cooper", "Mitchell", "Joshua",
        "Declan", "Flynn", "Riley", "Blake", "Tyler"
    ],
    "oceania_nz": [
        "James", "Oliver", "William", "Jack", "Liam", "Thomas", "Noah",
        "Lachlan", "Hunter", "Daniel", "Cooper", "Finn", "Sam", "Angus",
        "Hamish", "Fletcher", "Riley"
    ],
}

# ─── Last Names by Region ─────────────────────────────────────────────────

LAST_NAMES = {
    "europe_uk": [
        "Smith", "Jones", "Williams", "Taylor", "Davies", "Brown", "Wilson",
        "Evans", "Thomas", "Johnson", "Roberts", "Walker", "Wright", "Clark",
        "Hall", "Turner", "Adams", "Scott", "King", "Green", "Baker", "Hill",
        "Cooper", "Reed", "Morgan", "Harris", "Cook", "Bell", "Price", "Wood",
        "Watson", "Bennett", "Ross", "Parker", "Young", "James", "Miller"
    ],
    "europe_de": [
        "Schmidt", "Müller", "Schneider", "Fischer", "Weber", "Wagner", "Becker",
        "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
        "Schröder", "Neumann", "Zimmermann", "Braun", "Krüger", "Hartmann",
        "Lange", "Werner", "Schmitz", "Krause", "Maier", "Lehmann", "Köhler",
    ],
    "europe_fr": [
        "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
        "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
        "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
        "Girard", "Andre", "Mercier", "Dupont", "Lambert", "Fontaine",
    ],
    "europe_it": [
        "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
        "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "Costa",
        "Mancini", "Barbieri", "Fontana", "Rinaldi", "Caruso", "Moretti",
        "Giordano", "De Luca", "Serra", "Fabbri", "Palumbo", "Rizzi",
    ],
    "europe_es": [
        "García", "Rodríguez", "Martínez", "López", "Sánchez", "Pérez",
        "González", "Fernández", "Jiménez", "Ruiz", "Hernández", "Díaz",
        "Moreno", "Álvarez", "Romero", "Alonso", "Navarro", "Torres",
        "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano",
    ],
    "europe_nl": [
        "van Dijk", "de Jong", "Visser", "Bakker", "Janssen", "De Boer",
        "van der Berg", "Mulder", "de Groot", "Vos", "Peters", "Hendriks",
        "Dekker", "Bos", "Vermeulen", "de Wit", "van Dam", "Prins",
        "Meijer", "Hofman", "Kuiper", "Smit", "Kramer",
    ],
    "europe_nordic": [
        "Andersen", "Johansson", "Nilsson", "Eriksson", "Larsson", "Olsson",
        "Karlsson", "Hansen", "Pedersen", "Jensen", "Christensen", "Nielsen",
        "Svensson", "Gustafsson", "Bergström", "Lindqvist", "Åström",
        "Lindgren", "Berg", "Møller", "Thomsen", "Rasmussen",
    ],
    "europe_east": [
        "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kamiński", "Lewandowski",
        "Zieliński", "Szymański", "Woźniak", "Kozłowski", "Ivanov", "Petrov",
        "Sidorov", "Kuznetsov", "Popov", "Vasiliev", "Mikhailov", "Novikov",
        "Fedorov", "Morozov", "Volkov", "Alexeev", "Lebedev", "Semenov",
    ],
    "south_america_br": [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Lima", "Alves",
        "Pereira", "Costa", "Ferreira", "Barbosa", "Carvalho", "Gomes",
        "Martins", "Ribeiro", "Dias", "Moreira", "Cardoso", "Araújo",
        "Mendes", "Cavalcanti", "Nascimento", "Vieira",
    ],
    "south_america_ar": [
        "González", "Rodríguez", "Fernández", "López", "Martínez", "García",
        "Pérez", "Romero", "Díaz", "Torres", "Álvarez", "Ruiz", "Moreno",
        "Medina", "Castillo", "Sánchez", "Giménez", "Acosta", "Benítez",
    ],
    "south_america_co": [
        "Rodríguez", "González", "Martínez", "García", "López", "Hernández",
        "Sánchez", "Pérez", "Torres", "Ramírez", "Díaz", "Moreno", "Ruiz",
        "Álvarez", "Gómez", "Castro", "Ortiz", "Chávez", "Reyes",
    ],
    "north_america_us": [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
        "Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris",
        "Martin", "Thompson", "Moore", "Allen", "Clark", "Lewis", "Lee",
        "Walker", "Hall", "Young", "King", "Wright", "Hill", "Scott",
    ],
    "north_america_ca": [
        "Smith", "Brown", "Tremblay", "Martin", "Roy", "Wilson", "Johnson",
        "Taylor", "MacDonald", "Williams", "Gagnon", "Jones", "Miller",
        "Davis", "Campbell", "Anderson", "Thomson", "Clark", "Murray",
        "Scott", "Reid", "Ross", "Young", "Wright", "McDonald",
    ],
    "north_america_mx": [
        "Hernández", "García", "Martínez", "López", "González", "Rodríguez",
        "Pérez", "Sánchez", "Ramírez", "Cruz", "Flores", "Castillo",
        "Reyes", "Morales", "Ortiz", "Gutiérrez", "Rivera", "Mendoza",
        "Torres", "Jiménez", "Moreno", "Vázquez", "Chávez",
    ],
    "asia_jp": [
        "Sato", "Suzuki", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura",
        "Ogawa", "Kato", "Yoshida", "Yamada", "Sasaki", "Yamaguchi",
        "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu", "Mori",
        "Abe", "Ikeda", "Hashimoto", "Ishikawa", "Ono",
    ],
    "asia_cn": [
        "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang",
        "Zhou", "Wu", "Xu", "Sun", "Hu", "Zhu", "Gao", "Lin", "He",
        "Guo", "Ma", "Luo", "Liang", "Song", "Zheng", "Xie", "Han",
        "Tang", "Cao", "Deng", "Peng", "Cai",
    ],
    "asia_kr": [
        "Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon",
        "Jang", "Lim", "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang",
        "Ahn", "Song", "Yoo", "Hong", "Moon", "Yang", "Bae",
    ],
    "asia_in": [
        "Sharma", "Singh", "Patel", "Kumar", "Gupta", "Verma", "Reddy",
        "Joshi", "Das", "Nair", "Choudhury", "Mukherjee", "Rao", "Banerjee",
        "Mehta", "Saha", "Desai", "Sen", "Agarwal", "Pillai", "Iyer",
        "Bose", "Malhotra", "Srivastava", "Menon", "Chopra",
    ],
    "asia_se": [
        "Thongchai", "Srisawat", "Chaiyaporn", "Boonmee", "Ratanapong",
        "Nguyen", "Tran", "Le", "Pham", "Huynh", "Hoang", "Ngo", "Dang",
        "Vu", "Bui", "Do", "Wijaya", "Santoso", "Pratama", "Saputra",
    ],
    "africa_za": [
        "Nkosi", "Botha", "Mokoena", "van der Merwe", "Naidoo", "Dlamini",
        "Zulu", "van Wyk", "Khumalo", "Sithole", "Pretorius", "Mahlangu",
        "Fourie", "Ngubane", "Coetzee", "Mthembu", "Zondi", "Kunene",
    ],
    "africa_ng": [
        "Okafor", "Nwachukwu", "Okonkwo", "Eze", "Nwosu", "Ikechi",
        "Ogunlade", "Adebayo", "Olawale", "Ogunbiyi", "Emenike", "Abubakar",
        "Okoro", "Chukwu", "Onyema", "Ugwu", "Nnamdi", "Onyekachi",
    ],
    "africa_ke": [
        "Mwangi", "Kamau", "Njuguna", "Njoroge", "Wanjiku", "Mutua",
        "Kariuki", "Ochieng", "Wafula", "Chebet", "Kiprop", "Kipkemboi",
        "Kiprono", "Wekesa", "Barasa", "Wanjala", "Masinde",
    ],
    "africa_ma": [
        "El Amrani", "Ben Ali", "El Idrissi", "El Haddad", "Bennani",
        "El Fassi", "El Bakkali", "Ouaziz", "El Mansouri", "Fahim",
        "Alami", "Zeroual", "Bencheikh", "El Ouafi", "El Moutawakil",
    ],
    "oceania_au": [
        "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson",
        "White", "Martin", "Anderson", "Thompson", "Harris", "Thomas",
        "Walker", "Moore", "Kelly", "King", "Green", "Davies", "Miller",
        "Cooper", "Campbell", "Hughes", "Parker", "Edwards",
    ],
    "oceania_nz": [
        "Smith", "Williams", "Jones", "Brown", "Taylor", "Wilson", "Johnson",
        "Davies", "Thomas", "Thompson", "Anderson", "Harris", "Martin",
        "Walker", "Clark", "White", "Hall", "King", "Wright", "Scott",
        "McLeod", "McKenzie", "Fletcher", "Murray", "Cameron",
    ],
}

# ─── Region to sub-region mapping ─────────────────────────────────────────

REGION_MAP = {
    "europe": {
        "weight": 0.40,
        "sub_regions": {
            "europe_uk": 0.20,
            "europe_de": 0.18,
            "europe_fr": 0.16,
            "europe_it": 0.14,
            "europe_es": 0.12,
            "europe_nl": 0.05,
            "europe_nordic": 0.08,
            "europe_east": 0.07,
        }
    },
    "south_america": {
        "weight": 0.15,
        "sub_regions": {
            "south_america_br": 0.40,
            "south_america_ar": 0.25,
            "south_america_co": 0.20,
            "north_america_mx": 0.15,  # shared
        }
    },
    "north_america": {
        "weight": 0.15,
        "sub_regions": {
            "north_america_us": 0.60,
            "north_america_ca": 0.25,
            "north_america_mx": 0.15,
        }
    },
    "asia": {
        "weight": 0.15,
        "sub_regions": {
            "asia_jp": 0.20,
            "asia_cn": 0.25,
            "asia_kr": 0.15,
            "asia_in": 0.20,
            "asia_se": 0.20,
        }
    },
    "africa": {
        "weight": 0.10,
        "sub_regions": {
            "africa_za": 0.25,
            "africa_ng": 0.25,
            "africa_ke": 0.20,
            "africa_ma": 0.30,
        }
    },
    "oceania": {
        "weight": 0.05,
        "sub_regions": {
            "oceania_au": 0.65,
            "oceania_nz": 0.35,
        }
    },
}

# ISO country codes for each sub-region
SUB_REGION_COUNTRIES = {
    "europe_uk": "UK", "europe_de": "DE", "europe_fr": "FR",
    "europe_it": "IT", "europe_es": "ES", "europe_nl": "NL",
    "europe_nordic": "SE", "europe_east": "PL",
    "south_america_br": "BR", "south_america_ar": "AR",
    "south_america_co": "CO",
    "north_america_us": "US", "north_america_ca": "CA",
    "north_america_mx": "MX",
    "asia_jp": "JP", "asia_cn": "CN", "asia_kr": "KR",
    "asia_in": "IN", "asia_se": "TH",
    "africa_za": "ZA", "africa_ng": "NG", "africa_ke": "KE",
    "africa_ma": "MA",
    "oceania_au": "AU", "oceania_nz": "NZ",
}


class NameGenerator:
    """Generates realistic racing driver names."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def _pick_region(self) -> tuple[str, str]:
        """Pick a region and sub-region based on weights."""
        region_name = self.rng.choices(
            list(REGION_MAP.keys()),
            weights=[r["weight"] for r in REGION_MAP.values()]
        )[0]
        region = REGION_MAP[region_name]
        sub_name = self.rng.choices(
            list(region["sub_regions"].keys()),
            weights=list(region["sub_regions"].values())
        )[0]
        return region_name, sub_name

    def pick_sub_region(self) -> str:
        """Pick a sub-region directly."""
        _, sub = self._pick_region()
        return sub

    def pick_sub_region_from(self, region_name: str) -> str:
        """Pick a sub-region from a specific region."""
        region = REGION_MAP[region_name]
        return self.rng.choices(
            list(region["sub_regions"].keys()),
            weights=list(region["sub_regions"].values())
        )[0]

    def get_country(self, sub_region: str) -> str:
        """Get ISO country code for a sub-region."""
        return SUB_REGION_COUNTRIES.get(sub_region, "UK")

    def generate_name(self, sub_region: Optional[str] = None) -> dict:
        """Generate a full driver name.
        
        Returns:
            dict with keys: first_name, last_name, nationality, sub_region
        """
        if sub_region is None:
            _, sub_region = self._pick_region()

        first_names = FIRST_NAMES.get(sub_region, FIRST_NAMES["europe_uk"])
        last_names = LAST_NAMES.get(sub_region, LAST_NAMES["europe_uk"])

        first = self.rng.choice(first_names)
        last = self.rng.choice(last_names)
        nationality = SUB_REGION_COUNTRIES.get(sub_region, "UK")

        return {
            "first_name": first,
            "last_name": last,
            "nationality": nationality,
            "sub_region": sub_region,
        }

    def generate_multiple(self, count: int, region_bias: Optional[str] = None) -> list[dict]:
        """Generate multiple names, optionally biased toward a region."""
        names = []
        for _ in range(count):
            if region_bias and self.rng.random() < 0.4:
                sub = self.pick_sub_region_from(region_bias)
            else:
                _, sub = self._pick_region()
            names.append(self.generate_name(sub))
        return names

    def set_seed(self, seed: int):
        self.rng = random.Random(seed)
