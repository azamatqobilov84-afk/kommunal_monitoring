"""
O'zbekiston Respublikasi — viloyatlar va tumanlar ma'lumotlari.
Click ilovasidagidek kaskad tanlash uchun ishlatiladi.
"""

UZBEKISTAN_LOCATIONS = {
    'Toshkent shahri': [
        'Bektemir tumani', 'Chilonzor tumani', 'Mirobod tumani',
        "Mirzo Ulug'bek tumani", 'Olmazor tumani', 'Sergeli tumani',
        'Shayxontohur tumani', 'Uchtepa tumani', 'Yakkasaroy tumani',
        'Yashnobod tumani', 'Yunusobod tumani', 'Yangihayot tumani',
    ],
    'Toshkent viloyati': [
        'Bekobod shahri', 'Bekobod tumani', "Bo'ka tumani",
        "Bo'stonliq tumani", 'Chinoz tumani', 'Ohangaron shahri',
        'Ohangaron tumani', "Oqqo'rg'on tumani", 'Parkent tumani',
        'Piskent tumani', 'Quyichirchiq tumani', "O'rtachirchiq tumani",
        'Yuqorichirchiq tumani', "Yangiyo'l shahri", "Yangiyo'l tumani",
        'Zangiota tumani', 'Toshkent tumani', 'Nurafshon shahri',
        'Olmaliq shahri', 'Angren shahri', 'Chirchiq shahri',
    ],
    'Andijon viloyati': [
        'Andijon shahri', 'Andijon tumani', 'Asaka shahri', 'Asaka tumani',
        "Baliqchi tumani", "Bo'ston tumani", 'Buloqboshi tumani',
        'Izboskan tumani', 'Jalaquduq tumani', "Xo'jaobod tumani",
        'Marhamat tumani', "Oltinko'l tumani", 'Paxtaobod tumani',
        "Qo'rg'ontepa tumani", 'Shahrixon tumani', "Ulug'nor tumani",
        "Xonobod shahri",
    ],
    'Buxoro viloyati': [
        'Buxoro shahri', 'Buxoro tumani', "G'ijduvon tumani",
        'Jondor tumani', 'Kogon shahri', 'Kogon tumani', 'Olot tumani',
        'Peshku tumani', "Qorako'l tumani", "Qorovulbozor tumani",
        'Romitan tumani', 'Shofirkon tumani', 'Vobkent tumani',
    ],
    "Farg'ona viloyati": [
        'Beshariq tumani', "Bag'dod tumani", 'Buvayda tumani',
        "Dang'ara tumani", "Farg'ona shahri", "Farg'ona tumani",
        'Furqat tumani', "Marg'ilon shahri", 'Oltiariq tumani',
        "O'zbekiston tumani", 'Quva tumani', 'Quvasoy shahri',
        'Rishton tumani', "So'x tumani", 'Toshloq tumani',
        "Uchko'prik tumani", "Qo'qon shahri", 'Yozyovon tumani',
    ],
    'Jizzax viloyati': [
        'Arnasoy tumani', 'Baxmal tumani', "Do'stlik tumani",
        'Forish tumani', "G'allaorol tumani", 'Jizzax shahri',
        'Jizzax tumani', "Mirzacho'l tumani", 'Paxtakor tumani',
        'Yangiobod tumani', 'Zafarobod tumani', 'Zarbdor tumani',
        'Zomin tumani', "Sharof Rashidov tumani",
    ],
    'Xorazm viloyati': [
        "Bog'ot tumani", 'Gurlan tumani', 'Hazorasp tumani',
        'Xiva shahri', 'Xiva tumani', 'Xonqa tumani',
        "Qo'shko'pir tumani", 'Shovot tumani', 'Urganch shahri',
        'Urganch tumani', 'Yangiariq tumani', 'Yangibozor tumani',
        'Tuproqqala tumani',
    ],
    'Namangan viloyati': [
        'Chortoq tumani', 'Chust tumani', 'Kosonsoy tumani',
        'Mingbuloq tumani', 'Namangan shahri', 'Namangan tumani',
        'Norin tumani', 'Pop tumani', "To'raqo'rg'on tumani",
        "Uchqo'rg'on tumani", 'Uychi tumani', "Yangiqo'rg'on tumani",
        "Davlatobod tumani",
    ],
    'Navoiy viloyati': [
        'Karmana tumani', 'Konimex tumani', 'Navbahor tumani',
        'Navoiy shahri', 'Nurota tumani', 'Qiziltepa tumani',
        'Tomdi tumani', "Uchquduq tumani", 'Xatirchi tumani',
        'Zarafshon shahri',
    ],
    'Qashqadaryo viloyati': [
        'Chiroqchi tumani', 'Dehqonobod tumani', "G'uzor tumani",
        'Kasbi tumani', 'Kitob tumani', 'Koson tumani',
        'Qamashi tumani', 'Qarshi shahri', 'Qarshi tumani',
        'Mirishkor tumani', 'Muborak tumani', 'Nishon tumani',
        'Shahrisabz shahri', 'Shahrisabz tumani', "Yakkabog' tumani",
    ],
    "Qoraqalpog'iston Respublikasi": [
        'Amudaryo tumani', 'Beruniy tumani', "Bo'zatov tumani",
        'Chimboy tumani', 'Ellikqala tumani', 'Kegeyli tumani',
        "Mo'ynoq tumani", 'Nukus shahri', 'Nukus tumani',
        "Qanliko'l tumani", "Qorao'zak tumani", "Qo'ng'irot tumani",
        'Shumanay tumani', 'Taxiatosh tumani', "Taxtako'pir tumani",
        "To'rtko'l tumani", "Xo'jayli tumani",
    ],
    'Samarqand viloyati': [
        "Bulung'ur tumani", 'Ishtixon tumani', 'Jomboy tumani',
        "Kattaqo'rg'on shahri", "Kattaqo'rg'on tumani", 'Narpay tumani',
        'Nurobod tumani', 'Oqdaryo tumani', 'Paxtachi tumani',
        'Payariq tumani', "Pastdarg'om tumani", "Qo'shrabot tumani",
        'Samarqand shahri', 'Samarqand tumani', 'Tayloq tumani',
        'Urgut tumani', 'Urgut shahri',
    ],
    'Sirdaryo viloyati': [
        'Boyovut tumani', 'Guliston shahri', 'Guliston tumani',
        'Mirzaobod tumani', 'Oqoltin tumani', 'Sayxunobod tumani',
        'Sardoba tumani', 'Sirdaryo tumani', 'Xovos tumani',
        'Yangiyer shahri', 'Shirin shahri', "Boyovut tumani",
    ],
    'Surxondaryo viloyati': [
        'Angor tumani', 'Bandixon tumani', 'Boysun tumani',
        'Denov tumani', "Jarqo'rg'on tumani", 'Muzrabot tumani',
        'Oltinsoy tumani', 'Qiziriq tumani', "Qumqo'rg'on tumani",
        'Sariosiyo tumani', 'Sherobod tumani', "Sho'rchi tumani",
        'Termiz shahri', 'Termiz tumani', 'Uzun tumani',
    ],
}

# Region tanlash uchun choices (ModelChoiceField uchun)
REGION_CHOICES = [(name, name) for name in UZBEKISTAN_LOCATIONS.keys()]


def get_districts(region):
    """Berilgan viloyatga tegishli tumanlar ro'yxatini qaytaradi."""
    return UZBEKISTAN_LOCATIONS.get(region, [])


def get_all_regions():
    return list(UZBEKISTAN_LOCATIONS.keys())
