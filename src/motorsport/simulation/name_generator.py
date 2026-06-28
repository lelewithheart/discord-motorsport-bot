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
        "Max", "Leo", "Oscar", "Archie", "Theo", "Freddie", "Harvey",
        "Toby", "Finley", "Sebastian", "Arthur", "Albie", "Harrison",
        "Rex", "Louie", "Frankie", "Stanley", "Tommy", "Teddy", "Alfie",
        "Elliot", "Caleb"
    ],
    "europe_de": [
        "Finn", "Leon", "Lukas", "Maximilian", "Felix", "Jonas", "Niklas",
        "Luca", "Tim", "Lukas", "Elias", "Paul", "Julian", "Fabian",
        "Luis", "Noah", "Ben", "David", "Simon", "Anton", "Emil",
        "Johann", "Karl", "Hermann", "Friedrich", "Otto", "Klaus",
        "Franz", "Dieter", "Günther", "Ralf", "Stefan", "Markus",
        "Andreas", "Jürgen", "Wolfgang"
    ],
    "europe_fr": [
        "Lucas", "Hugo", "Louis", "Gabriel", "Raphaël", "Jules", "Adam",
        "Arthur", "Maël", "Léo", "Nathan", "Mathis", "Ethan", "Tom",
        "Théo", "Nolan", "Clément", "Antoine", "Alexandre", "Quentin",
        "Valentin", "Julien", "Romain", "Florian", "Nicolas", "Jérémy",
        "Cédric", "Guillaume", "Sébastien", "Bastien", "Kylian",
        "Matthieu", "Rémy", "Amaury", "Baptiste"
    ],
    "europe_it": [
        "Leonardo", "Lorenzo", "Francesco", "Alessandro", "Andrea", "Matteo",
        "Luca", "Gabriele", "Riccardo", "Tommaso", "Edoardo", "Marco",
        "Antonio", "Federico", "Giovanni", "Raffaele", "Daniele",
        "Alessio", "Simone", "Fabio", "Gianni", "Paolo", "Stefano",
        "Michele", "Enrico", "Luigi", "Mario", "Angelo", "Vittorio",
        "Giuseppe", "Cristian", "Davide", "Massimo", "Franco"
    ],
    "europe_es": [
        "Mateo", "Pablo", "Alejandro", "Daniel", "Leo", "Lucas", "Manuel",
        "Hugo", "Diego", "Javier", "Alvaro", "Carlos", "Miguel", "Sergio",
        "Jorge", "Raul", "Ivan", "Marcos", "Adrián", "Marcos",
        "Gonzalo", "Enrique", "Francisco", "Alberto", "Fernando",
        "Jaime", "Rubén", "Vicente", "Samuel", "David", "Pedro",
        "Ismael", "Guillermo"
    ],
    "europe_nl": [
        "Daan", "Sem", "Lucas", "Finn", "Levi", "Bram", "Jesse", "Thomas",
        "Tim", "Max", "Ruben", "Lars", "Sven", "Niels", "Wout", "Joost",
        "Milan", "Jasper", "Dylan", "Ryan", "Joris", "Thijs", "Bas",
        "Gijs", "Wouter", "Martijn", "Koen", "Robin", "Stijn", "Pim",
        "Hugo", "Teun", "Floris", "Hidde"
    ],
    "europe_nordic": [
        "Elias", "Oliver", "Liam", "William", "Noah", "Oscar", "Hugo",
        "Axel", "Erik", "Lars", "Anders", "Magnus", "Sven", "Björn",
        "Henrik", "Nils", "Olof", "Karl", "Mikael", "Mats", "Johan",
        "Per", "Tommy", "Fredrik", "Rasmus", "Emil", "Olle", "Måns",
        "Samuel", "Viktor", "Simon", "Einar", "Arne", "Olav",
        "Trygve", "Oskar"
    ],
    "europe_east": [
        "Jakub", "Jan", "Tomas", "Piotr", "Mikhail", "Dmitri", "Andrei",
        "Ivan", "Nikolai", "Alexei", "Pavel", "Yuri", "Artem", "Sergei",
        "Krzysztof", "Marek", "Adam", "Mateusz", "Milan", "Lukas",
        "Petr", "Vladimir", "Oleg", "Boris", "Roman", "Viktor",
        "Mykola", "Dmytro", "Taras", "Bohdan", "Sergey", "Konstantin",
        "Grigoriy", "Yaroslav", "Stanislav"
    ],
    "south_america_br": [
        "Carlos", "Lucas", "Gabriel", "Rafael", "Felipe", "Bruno",
        "Thiago", "Vinicius", "Gustavo", "Paulo", "Eduardo", "Marcos",
        "Pedro", "Leonardo", "André", "Diego", "Luis", "Guilherme",
        "Alex", "Fabrício", "Marcelo", "Renato", "Ricardo", "Márcio",
        "José", "Antônio", "João", "Francisco", "Roger", "Danilo",
        "Alexandre", "Caio", "Igor", "Ronaldo", "Maurício"
    ],
    "south_america_ar": [
        "Santiago", "Mateo", "Lautaro", "Bruno", "Franco", "Emiliano",
        "Joaquín", "Nicolás", "Luciano", "Alejandro", "Martín", "Juan",
        "Diego", "Valentino", "Federico", "Agustín", "Tomas",
        "Facundo", "Ignacio", "Matías", "Francisco", "Gonzalo",
        "Lucas", "Federico", "Agustín", "Mariano", "Pablo",
        "Ezequiel", "Ramiro", "Leandro", "Julian", "Esteban",
        "Sebastian", "Máximo"
    ],
    "south_america_co": [
        "Santiago", "Carlos", "Andrés", "Juan", "Miguel", "Pablo",
        "Daniel", "Sebastián", "Felipe", "Jorge", "Oscar", "Camilo",
        "Luis", "David", "Manuel", "Esteban", "Julian", "Andrés",
        "Simón", "Nicolás", "Mateo", "Jerónimo", "Emilio", "José",
        "Julián", "Marco", "Tomás", "Gabriel", "Samuel",
        "Jairo", "Hernán"
    ],
    "north_america_us": [
        "Ethan", "Jackson", "Mason", "Luke", "Ryan", "Tyler", "Dylan",
        "Hunter", "Carson", "Landon", "Carter", "Logan", "Jake", "Cole",
        "Chase", "Connor", "Aaron", "Jason", "Bradley", "Justin",
        "Kevin", "Brandon", "Nathan", "Nicholas", "Matthew",
        "Christopher", "Andrew", "Joshua", "Daniel", "Zachary",
        "Evan", "Kyle", "Austin", "Cameron"
    ],
    "north_america_ca": [
        "Liam", "Noah", "Oliver", "Ethan", "Lucas", "Jack", "James",
        "Benjamin", "Logan", "Owen", "William", "Dylan", "Ryan", "Carter",
        "Nathan", "Connor", "Samuel", "Matthew", "Jacob", "Alexander",
        "Ethan", "Nathan", "Samuel", "Ryan", "Carter", "William",
        "Daniel", "Thomas", "Nicholas", "Sebastian", "Evan",
        "Benjamin", "Owen", "Adam", "Maxwell"
    ],
    "north_america_mx": [
        "Santiago", "Mateo", "Diego", "Luis", "Carlos", "Miguel",
        "Alejandro", "Emiliano", "Juan", "Pablo", "Fernando", "Andrés",
        "Eduardo", "Ricardo", "Javier", "Diego", "Emiliano", "Mateo",
        "Santiago", "Ángel", "Rodrigo", "Manuel", "José", "Francisco",
        "Héctor", "Jorge", "Rafael", "Alberto", "Raúl", "Víctor",
        "Rubén", "Mario"
    ],
    "asia_jp": [
        "Kenji", "Hiroshi", "Takashi", "Yuki", "Sho", "Ryo", "Kenta",
        "Daiki", "Shin", "Kazuki", "Takeshi", "Ryota", "Koji", "Yuta",
        "Satoshi", "Taro", "Jun", "Ren", "Haruki", "Yuma", "Kaito",
        "Riku", "Sora", "Yuito", "Itsuki", "Rintaro", "Genji",
        "Hideki", "Makoto", "Shinji", "Akira", "Ryuji", "Tsubasa",
        "Yoshiki", "Hayato"
    ],
    "asia_cn": [
        "Wei", "Chen", "Ming", "Hao", "Jun", "Yang", "Lei", "Kai",
        "Peng", "Tao", "Zhi", "Long", "Qiang", "Feng", "Bin", "Lin",
        "Xin", "Lei", "Dong", "Jian", "Xia", "Yun", "Bo", "Jin",
        "Zhen", "Tian", "Ming", "Yi", "Hai", "Wei", "Shen", "Jie",
        "An", "Xiang", "Song", "Yong"
    ],
    "asia_kr": [
        "Min-Jun", "Seo-Jun", "Ji-Ho", "Hyun-Woo", "Jae-Won", "Sang-Min",
        "Dong-Hyun", "Young-Jae", "Jin-Ho", "Tae-Yang", "Kwang-Soo",
        "Jung-Hwan", "Woo-Jin", "Han-Sol", "Joon-Ho", "Hyun-Woo",
        "Yun", "Seung-Min", "Ji-Hoon", "Sung-Ho", "Min-Kyu",
        "Dong-Hyuk", "Tae-Soo", "Jae-Hwan", "Woo-Sung", "Sang-Hoon",
        "Yeon-Soo", "Hae-Jin", "Soo-Hyun"
    ],
    "asia_in": [
        "Arjun", "Rohan", "Vikram", "Aryan", "Karan", "Dev", "Ravi",
        "Aditya", "Rahul", "Amit", "Siddharth", "Raj", "Aakash", "Kunal",
        "Vivek", "Manish", "Harsh", "Nikhil", "Pranav", "Ishan",
        "Dhruv", "Kabir", "Yash", "Rohit", "Aniket", "Sameer",
        "Shiv", "Tarun", "Neel", "Abhishek", "Gaurav", "Sahil",
        "Surya", "Krishna", "Varun", "Akash"
    ],
    "asia_se": [
        "Somchai", "Thanawat", "Anurak", "Kittipat", "Adisak", "Minh",
        "Tuan", "Phong", "Huy", "Duc", "Anh", "Budi", "Agus", "Hendra",
        "Dwi", "Rizky", "Nattapong", "Somsak", "Prasert", "Somchai",
        "Wichai", "Chaiwat", "Panya", "Krit", "Anuwat", "Sakda",
        "Thaworn", "Phan", "Sokhom", "Rath", "Sovann", "Borey",
        "Chandara"
    ],
    "africa_za": [
        "Thabo", "Lungile", "Sipho", "Bongani", "Musa", "Sizwe",
        "Nkosi", "Mandla", "Jabulani", "Kagiso", "Tendai", "Dumisani",
        "Lwazi", "Vusumuzi", "Sipho", "Lungelo", "Nkosana", "Ayanda",
        "Sbusiso", "Themba", "Mxolisi", "Buhle", "Minenhle", "Xolani",
        "Zamani", "Sandile", "Wandile", "Sibonelo", "Mondli",
        "Philani", "Sanele"
    ],
    "africa_ng": [
        "Chidi", "Kofi", "Emeka", "Oluwaseun", "Chinedu", "Tunde",
        "Kwame", "Adebayo", "Femi", "Kehinde", "Tajudeen", "Obinna",
        "Chibueze", "Eze", "Uchenna", "Chibuzo", "Chuma", "Onyedika",
        "Ekene", "Okechukwu", "Osita", "Chijioke", "Ifeanyi",
        "Nnamdi", "Onyekachi", "Kelechi", "Ebuka", "Chigozie",
        "Somtochukwu", "Akachukwu", "Chukwudi"
    ],
    "africa_ke": [
        "John", "David", "Peter", "James", "Joseph", "Daniel", "Samuel",
        "Patrick", "Stephen", "Michael", "Paul", "George", "Thomas",
        "James", "Francis", "Simon", "Kennedy", "Samuel", "Richard",
        "Stephen", "Geoffrey", "Jackson", "Nicholas", "Moses",
        "Erick", "Collins", "Benson", "Meshack", "Wilson",
        "Frederick"
    ],
    "africa_ma": [
        "Ahmed", "Mohammed", "Hassan", "Youssef", "Omar", "Ali", "Karim",
        "Rachid", "Soulaimane", "Amine", "Mehdi", "Hicham", "Sami",
        "Said", "Abdellah", "Abdelilah", "Abdelkrim", "Mounir",
        "Driss", "Jawad", "Noureddine", "Aziz", "Khalid", "Alaa",
        "Ismail", "Yassin", "Adnan", "Murad", "Abdul", "Nadir"
    ],
    "oceania_au": [
        "Jack", "Oliver", "William", "James", "Thomas", "Liam", "Noah",
        "Ethan", "Lucas", "Harrison", "Cooper", "Mitchell", "Joshua",
        "Declan", "Flynn", "Riley", "Blake", "Tyler", "Lachlan",
        "Angus", "Fletcher", "Hamish", "Harrison", "Archie", "Hugo",
        "Xavier", "Charlie", "Patrick", "Joseph", "Tom", "Max",
        "Jake", "Sam", "Oliver", "Thomas"
    ],
    "oceania_nz": [
        "James", "Oliver", "William", "Jack", "Liam", "Thomas", "Noah",
        "Lachlan", "Hunter", "Daniel", "Cooper", "Finn", "Sam", "Angus",
        "Hamish", "Fletcher", "Riley", "Finn", "Luca", "Morgan",
        "Jake", "Liam", "Cody", "Hemi", "Manu", "Sione", "Dylan",
        "Manaia", "Ariki", "Wiremu", "Tama", "Nikau", "Rawiri",
        "Logan"
    ],
    "europe_at": [
        "Felix", "Sebastian", "Florian", "Julian", "Jakob", "Alexander",
        "Philipp", "Maximilian", "Moritz", "David", "Simon", "Dominik",
        "Lukas", "Christoph", "Andreas", "Peter"
    ],
    "europe_ch": [
        "Noah", "Liam", "Elias", "Leon", "Luca", "Finn", "Luis",
        "Julian", "Max", "David", "Nils", "Sven", "Marco", "Yannick",
        "Pascal", "Raphael", "Joel", "Gian"
    ],
    "europe_pt": [
        "João", "Miguel", "Tiago", "Diogo", "André", "Pedro", "Rui",
        "Bruno", "Carlos", "Nuno", "Ricardo", "Fábio", "Hugo",
        "Jorge", "Luís", "José", "Manuel", "David"
    ],
    "europe_be": [
        "Liam", "Noah", "Arthur", "Jules", "Louis", "Finn", "Lucas",
        "Ruben", "Wout", "Jasper", "Guillaume", "Lars", "Victor",
        "Théo", "Mathis", "Daan", "Tuur", "Siebe"
    ],
    "europe_ie": [
        "Patrick", "Sean", "Conor", "Darragh", "Cillian", "Declan",
        "Oisín", "Eoin", "Cian", "Niall", "Rory", "Fionn", "Shane",
        "Liam", "Cathal", "Tadhg", "Ronan", "Aidan"
    ],
    "asia_my": [
        "Ahmad", "Muhammad", "Aiman", "Hafiz", "Irfan", "Faiz",
        "Amirul", "Azizul", "Farid", "Shahrizal", "Syafiq", "Adib",
        "Iskandar", "Rizwan", "Firdaus"
    ],
}

# ─── Last Names by Region ─────────────────────────────────────────────────

LAST_NAMES = {
    "europe_uk": [
        "Smith", "Jones", "Williams", "Taylor", "Davies", "Brown", "Wilson",
        "Evans", "Thomas", "Johnson", "Roberts", "Walker", "Wright", "Clark",
        "Hall", "Turner", "Adams", "Scott", "King", "Green", "Baker", "Hill",
        "Cooper", "Reed", "Morgan", "Harris", "Cook", "Bell", "Price", "Wood",
        "Watson", "Bennett", "Ross", "Parker", "Young", "James", "Miller",
        "Mitchell", "Carter", "Murphy", "Bailey", "Richardson", "Cox",
        "Howard", "Ward", "Brooks", "West", "Cole", "Fox", "Harper",
        "Hart", "Knight", "Stone", "Wells"
    ],
    "europe_de": [
        "Schmidt", "Müller", "Schneider", "Fischer", "Weber", "Wagner", "Becker",
        "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
        "Schröder", "Neumann", "Zimmermann", "Braun", "Krüger", "Hartmann",
        "Lange", "Werner", "Schmitz", "Krause", "Maier", "Lehmann", "Köhler",
        "Meyer", "Schulz", "Jäger", "Kaiser", "Hübner", "Böhm", "Voigt",
        "Kunz", "Engel", "Pohl", "Vogel", "Arnold", "Schuster", "Brandt",
        "Busch", "Seidel", "Reuter"
    ],
    "europe_fr": [
        "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit",
        "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel",
        "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
        "Girard", "Andre", "Mercier", "Dupont", "Lambert", "Fontaine",
        "Blanchard", "Henry", "Garnier", "Chevalier", "François",
        "Legrand", "Gauthier", "Millet", "Perrin", "Colin", "Boyer",
        "Lemoine", "Caron", "Charpentier", "Poirier", "Renard",
        "Marchand"
    ],
    "europe_it": [
        "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo",
        "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "Costa",
        "Mancini", "Barbieri", "Fontana", "Rinaldi", "Caruso", "Moretti",
        "Giordano", "De Luca", "Serra", "Fabbri", "Palumbo", "Rizzi",
        "Marini", "Parisi", "Martini", "Battaglia", "Ferraro",
        "Cattaneo", "Gentile", "Vitali", "Lombardi", "Villa",
        "Mariani", "Coppola", "Basile", "Pace", "Mazza", "Leo",
        "Carbone"
    ],
    "europe_es": [
        "García", "Rodríguez", "Martínez", "López", "Sánchez", "Pérez",
        "González", "Fernández", "Jiménez", "Ruiz", "Hernández", "Díaz",
        "Moreno", "Álvarez", "Romero", "Alonso", "Navarro", "Torres",
        "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano",
        "Flores", "Rubio", "Molina", "Cruz", "Ortiz", "Marín",
        "Iglesias", "Castro", "Gallego", "Reyes", "Cano", "Suárez",
        "Campos", "Muñoz", "Velasco", "Pastor", "Aguilar"
    ],
    "europe_nl": [
        "van Dijk", "de Jong", "Visser", "Bakker", "Janssen", "De Boer",
        "van der Berg", "Mulder", "de Groot", "Vos", "Peters", "Hendriks",
        "Dekker", "Bos", "Vermeulen", "de Wit", "van Dam", "Prins",
        "Meijer", "Hofman", "Kuiper", "Smit", "Kramer",
        "Jacobs", "Koning", "Willems", "Vink", "Brink",
        "Dijkstra", "Schepers", "Jansen", "Brouwer", "Koster",
        "Kuipers", "van der Heijden", "Rutten", "Veenstra",
        "Molenaar", "van Loon"
    ],
    "europe_nordic": [
        "Andersen", "Johansson", "Nilsson", "Eriksson", "Larsson", "Olsson",
        "Karlsson", "Hansen", "Pedersen", "Jensen", "Christensen", "Nielsen",
        "Svensson", "Gustafsson", "Bergström", "Lindqvist", "Åström",
        "Lindgren", "Berg", "Møller", "Thomsen", "Rasmussen",
        "Ekström", "Lundqvist", "Björklund", "Åberg", "Holm",
        "Nygaard", "Mortensen", "Norgaard", "Strandberg", "Norberg",
        "Dahlberg", "Lindeberg", "Sørensen", "Holgersen", "Bech",
        "Falk", "Skov"
    ],
    "europe_east": [
        "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kamiński", "Lewandowski",
        "Zieliński", "Szymański", "Woźniak", "Kozłowski", "Ivanov", "Petrov",
        "Sidorov", "Kuznetsov", "Popov", "Vasiliev", "Mikhailov", "Novikov",
        "Fedorov", "Morozov", "Volkov", "Alexeev", "Lebedev", "Semenov",
        "Kowalczyk", "Zalewski", "Jankowski", "Kaczmarek", "Piotrowski",
        "Grabowski", "Pawlak", "Michalski", "Wróbel", "Romanov",
        "Kuzmin", "Sorokin", "Belyakov", "Kozlov", "Stepanov",
        "Tikhonov", "Frolov"
    ],
    "south_america_br": [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Lima", "Alves",
        "Pereira", "Costa", "Ferreira", "Barbosa", "Carvalho", "Gomes",
        "Martins", "Ribeiro", "Dias", "Moreira", "Cardoso", "Araújo",
        "Mendes", "Cavalcanti", "Nascimento", "Vieira",
        "Cunha", "Campos", "Teixeira", "Rocha", "Macedo",
        "Monteiro", "Barros", "Freitas", "Sousa", "Nunes",
        "Correia", "Rezende", "Xavier", "Batista", "Bezerra",
        "Coutinho", "Azevedo"
    ],
    "south_america_ar": [
        "González", "Rodríguez", "Fernández", "López", "Martínez", "García",
        "Pérez", "Romero", "Díaz", "Torres", "Álvarez", "Ruiz", "Moreno",
        "Medina", "Castillo", "Sánchez", "Giménez", "Acosta", "Benítez",
        "Mendoza", "Navarro", "Delgado", "Sosa", "Vega", "Campos",
        "Molina", "Cáceres", "Godoy", "Vera", "Luna", "Roldán",
        "Pereyra", "Carrizo", "Guerra", "Coronel", "Palacios"
    ],
    "south_america_co": [
        "Rodríguez", "González", "Martínez", "García", "López", "Hernández",
        "Sánchez", "Pérez", "Torres", "Ramírez", "Díaz", "Moreno", "Ruiz",
        "Álvarez", "Gómez", "Castro", "Ortiz", "Chávez", "Reyes",
        "Murillo", "Cardona", "Rojas", "Bermúdez", "Vargas",
        "Cifuentes", "Ospina", "Quintero", "Cárdenas", "Mendoza",
        "Palacios", "Pineda", "Londoño", "Correa", "Santamaría",
        "Zuleta", "Suárez"
    ],
    "north_america_us": [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
        "Wilson", "Anderson", "Taylor", "Thomas", "Jackson", "White", "Harris",
        "Martin", "Thompson", "Moore", "Allen", "Clark", "Lewis", "Lee",
        "Walker", "Hall", "Young", "King", "Wright", "Hill", "Scott",
        "Nelson", "Carter", "Mitchell", "Roberts", "Turner", "Phillips",
        "Campbell", "Parker", "Evans", "Edwards", "Collins", "Stewart",
        "Morris", "Rogers", "Reed", "Cook", "Morgan"
    ],
    "north_america_ca": [
        "Smith", "Brown", "Tremblay", "Martin", "Roy", "Wilson", "Johnson",
        "Taylor", "MacDonald", "Williams", "Gagnon", "Jones", "Miller",
        "Davis", "Campbell", "Anderson", "Thomson", "Clark", "Murray",
        "Scott", "Reid", "Ross", "Young", "Wright", "McDonald",
        "Bouchard", "Côté", "Pelletier", "Bélanger", "Lavoie",
        "Leblanc", "Ouellet", "Poirier", "Fortin", "Gagné",
        "Desjardins", "Boisvert", "Beaulieu", "Cloutier", "Caron",
        "Bergeron", "Plourde"
    ],
    "north_america_mx": [
        "Hernández", "García", "Martínez", "López", "González", "Rodríguez",
        "Pérez", "Sánchez", "Ramírez", "Cruz", "Flores", "Castillo",
        "Reyes", "Morales", "Ortiz", "Gutiérrez", "Rivera", "Mendoza",
        "Torres", "Jiménez", "Moreno", "Vázquez", "Chávez",
        "Ramos", "Guzmán", "Paredes", "Vargas", "Salazar",
        "Aguilar", "Rivas", "Mejía", "Muñoz", "Carrillo",
        "Delgado", "Soto", "Valencia", "Miranda", "Velázquez",
        "Osorio", "Cabrera"
    ],
    "asia_jp": [
        "Sato", "Suzuki", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura",
        "Ogawa", "Kato", "Yoshida", "Yamada", "Sasaki", "Yamaguchi",
        "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu", "Mori",
        "Abe", "Ikeda", "Hashimoto", "Ishikawa", "Ono",
        "Endo", "Takahashi", "Kobayashi", "Fujita", "Sakamoto",
        "Yoshikawa", "Murakami", "Okada", "Miyazaki", "Takeuchi",
        "Kawasaki", "Nishimura", "Sakai", "Kudo", "Miyamoto",
        "Nakajima", "Noguchi"
    ],
    "asia_cn": [
        "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang",
        "Zhou", "Wu", "Xu", "Sun", "Hu", "Zhu", "Gao", "Lin", "He",
        "Guo", "Ma", "Luo", "Liang", "Song", "Zheng", "Xie", "Han",
        "Tang", "Cao", "Deng", "Peng", "Cai",
        "Feng", "Shen", "Fan", "Tian", "Jiang", "Yao", "Jia",
        "Lu", "Hui", "Fu", "Yan", "Xiao", "Kong", "Chang",
        "Cheng", "Qiu", "Dai"
    ],
    "asia_kr": [
        "Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon",
        "Jang", "Lim", "Han", "Oh", "Seo", "Shin", "Kwon", "Hwang",
        "Ahn", "Song", "Yoo", "Hong", "Moon", "Yang", "Bae",
        "Shim", "Koo", "Suh", "Ryu", "Cha", "Noh", "Na",
        "Heo", "Ma", "Joo", "Chun", "Pyun", "Son",
        "Mun", "Woo", "Kil"
    ],
    "asia_in": [
        "Sharma", "Singh", "Patel", "Kumar", "Gupta", "Verma", "Reddy",
        "Joshi", "Das", "Nair", "Choudhury", "Mukherjee", "Rao", "Banerjee",
        "Mehta", "Saha", "Desai", "Sen", "Agarwal", "Pillai", "Iyer",
        "Bose", "Malhotra", "Srivastava", "Menon", "Chopra",
        "Devi", "Chauhan", "Yadav", "Walia", "Kapoor",
        "Gandhi", "Tiwari", "Bhatt", "Shenoy", "Kulkarni",
        "Mohan", "Mishra", "Kataria", "Pandey", "Trivedi",
        "Mahajan", "Ahuja"
    ],
    "asia_se": [
        "Thongchai", "Srisawat", "Chaiyaporn", "Boonmee", "Ratanapong",
        "Nguyen", "Tran", "Le", "Pham", "Huynh", "Hoang", "Ngo", "Dang",
        "Vu", "Bui", "Do", "Wijaya", "Santoso", "Pratama", "Saputra",
        "Chaichana", "Kaewkang", "Nakarin", "Sanguan", "Viroj",
        "Worapong", "Sutthiphong", "Theeraphong", "Kampol", "Somkiat",
        "Phromphong", "Wichian", "Sombat", "Praphan", "Adisorn",
        "Preeda", "Rojana"
    ],
    "africa_za": [
        "Nkosi", "Botha", "Mokoena", "van der Merwe", "Naidoo", "Dlamini",
        "Zulu", "van Wyk", "Khumalo", "Sithole", "Pretorius", "Mahlangu",
        "Fourie", "Ngubane", "Coetzee", "Mthembu", "Zondi", "Kunene",
        "Molefe", "Mkhize", "Ndlovu", "Mbatha", "Buthelezi", "Zwane",
        "Masango", "Xaba", "Mlamla", "Mthembu",
    ],
    "africa_ng": [
        "Okafor", "Nwachukwu", "Okonkwo", "Eze", "Nwosu", "Ikechi",
        "Ogunlade", "Adebayo", "Olawale", "Ogunbiyi", "Emenike", "Abubakar",
        "Okoro", "Chukwu", "Onyema", "Ugwu", "Nnamdi", "Onyekachi",
        "Okeke", "Ugwuoke", "Eze", "Obinna", "Onyishi", "Akabuogu",
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
    "europe_at": [
        "Gruber", "Huber", "Bauer", "Wagner", "Müller", "Pichler", "Steiner",
        "Weber", "Moser", "Mayr", "Hofer", "Egger", "Leitner", "Berger",
        "Fuchs", "Aigner", "Schmid", "Maier", "Haas", "Winkler",
        "Reiter", "Baumgartner", "Auer", "Köll", "Kreiner",
    ],
    "europe_ch": [
        "Meier", "Keller", "Schmid", "Brunner", "Weber", "Müller", "Fischer",
        "Gerber", "Bachmann", "Baumann", "Frei", "Moser", "Roth", "Stocker",
        "Huber", "Rüegg", "Graf", "Arnold", "Stalder", "Widmer", "Imhof",
        "Bühler", "Marti", "Lüthi",
    ],
    "europe_pt": [
        "Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Rodrigues",
        "Martins", "Sousa", "Fernandes", "Gonçalves", "Almeida", "Pinto",
        "Carvalho", "Ribeiro", "Costa", "Gomes", "Marques", "Neves", "Cruz",
        "Araújo", "Monteiro", "Cardoso", "Mendes", "Lopes",
    ],
    "europe_be": [
        "Peeters", "Maes", "Jacobs", "Willems", "Claes", "Mertens", "Goossens",
        "Wouters", "Vermeulen", "De Smet", "Vandenberg", "Van Dyck", "Aerts",
        "Hendrickx", "Desmet", "Van Damme", "Weyn", "Verstraeten", "Pauwels",
    ],
    "europe_ie": [
        "Murphy", "O'Brien", "Kelly", "Ryan", "Byrne", "Walsh", "O'Connor",
        "O'Sullivan", "McCarthy", "Doyle", "Gallagher", "Dunne", "Brennan",
        "Burke", "Collins", "Lyons", "Kavanagh", "Nolan", "Fitzgerald",
        "O'Neill", "Power", "Quinn", "Lynch",
    ],
    "asia_my": [
        "bin Abdullah", "bin Ismail", "bin Ahmad", "bin Ibrahim", "bin Hassan",
        "bin Ali", "bin Yusoff", "bin Othman", "bin Jaafar", "bin Saad",
        "bin Rahman", "bin Hashim", "bin Razak", "bin Malik", "bin Hamid",
    ],
}

# ─── Region to sub-region mapping ─────────────────────────────────────────

REGION_MAP = {
    "europe": {
        "weight": 0.40,
        "sub_regions": {
            "europe_uk": 0.13,
            "europe_de": 0.12,
            "europe_fr": 0.11,
            "europe_it": 0.10,
            "europe_es": 0.09,
            "europe_nl": 0.04,
            "europe_nordic": 0.06,
            "europe_east": 0.05,
            "europe_at": 0.06,
            "europe_ch": 0.05,
            "europe_pt": 0.04,
            "europe_be": 0.03,
            "europe_ie": 0.03,
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
            "asia_jp": 0.18,
            "asia_cn": 0.22,
            "asia_kr": 0.13,
            "asia_in": 0.18,
            "asia_se": 0.18,
            "asia_my": 0.11,
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
    "europe_at": "AT", "europe_ch": "CH", "europe_pt": "PT",
    "europe_be": "BE", "europe_ie": "IE",
    "south_america_br": "BR", "south_america_ar": "AR",
    "south_america_co": "CO",
    "north_america_us": "US", "north_america_ca": "CA",
    "north_america_mx": "MX",
    "asia_jp": "JP", "asia_cn": "CN", "asia_kr": "KR",
    "asia_in": "IN", "asia_se": "TH", "asia_my": "MY",
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
