from backend.models import db, Brand, BrandSynonym

def seed_brand_synonyms():
    brand_synonyms_data = {
        "Audi": ["AUDI", "Audi", "audi", "Ауди", "ауди"],
        "Avatr": ["AVATR", "Avatr", "avatr", "АватР", "аватр"],
        "BAIC": ["BAIC", "Baic", "baic", "БАИК", "баик", "Beijing Auto", "BEIJING AUTO"],
        "BMW": ["BMW", "Bmw", "bmw", "БМВ", "бмв", "Bayerische Motoren Werke", "BAYERISCHE MOTOREN WERKE"],
        "Buick": ["BUICK", "Buick", "buick", "Бьюик", "бьюик"],
        "BYD": ["BYD", "Byd", "byd", "БИД", "бид", "Build Your Dream", "BUILD YOUR DREAM", "Build your dream"],
        "Cadillac": ["CADILLAC", "Cadillac", "cadillac", "Кадиллак", "КАДИЛЛАК", "кадиллак"],
        "Changan": ["CHANGAN", "Changan", "changan", "Чанган", "ЧАНГАН", "чанган"],
        "Chery": ["CHERY", "Chery", "chery", "Чери", "ЧЕРИ", "чери"],
        "Chevrolet": ["CHEVROLET", "Chevrolet", "chevrolet", "Шевроле", "ШЕВРОЛЕ", "шевроле", "Chevy", "CHEVY"],
        "Citroen": ["CITROEN", "Citroen", "citroen", "Ситроен", "СИТРОЕН", "ситроен"],
        "Denza": ["DENZA", "Denza", "denza", "Денза", "ДЕНЗА", "денза"],
        "Dongfeng": ["DONGFENG", "Dongfeng", "dongfeng", "Донгфенг", "ДОНГФЕНГ", "донгфенг", "DFM", "dfm"],
        "Exeed": ["EXEED", "Exeed", "exeed", "Эксид", "ЭКСИД", "ексид"],
        "FAW": ["FAW", "Faw", "faw", "ФАВ", "фав", "First Automobile Works", "FIRST AUTOMOBILE WORKS"],
        "Ford": ["FORD", "Ford", "ford", "Форд", "ФОРД", "форд"],
        "Forthing": ["FORTHING", "Forthing", "forthing", "Фортинг", "ФОРТИНГ", "фортинг"],
        "GAC": ["GAC", "Gac", "gac", "ГАК", "гак", "Guangzhou Automobile Group", "GUANGZHOU AUTOMOBILE GROUP"],
        "Geely": ["GEELY", "Geely", "geely", "Джили", "ДЖИЛИ", "джили"],
        "Great Wall": ["GREAT WALL", "GREAT-WALL", "GREATWALL", "Great Wall", "Greatwall", "great wall", "greatwall", "Грейт Вол", "Грейт-Вол", "ГрейтВол"],
        "Haval": ["HAVAL", "Haval", "haval", "Хавейл", "ХАВЕЙЛ", "хавейл"],
        "HiPhi": ["HIPHI", "HiPhi", "hiphi", "ХайФай", "Хай-Фай", "ХайФай"],
        "Honda": ["HONDA", "Honda", "honda", "Хонда", "ХОНДА", "хонда"],
        "Hongqi": ["HONGQI", "Hongqi", "hongqi", "Хонгки", "ХОНГКИ", "хонгки", "Red Flag", "RED FLAG"],
        "Huawei": ["HUAWEI", "Huawei", "huawei", "Хуавей", "ХУАВЕЙ", "хуавей"],
        "Hyundai": ["HYUNDAI", "Hyundai", "hyundai", "Хендай", "ХЕНДАЙ", "хендай", "Хёндэ", "ХЁНДЭ"],
        "Infiniti": ["INFINITI", "Infiniti", "infiniti", "Инфинити", "ИНФИНИТИ", "инфинити"],
        "Jaguar": ["JAGUAR", "Jaguar", "jaguar", "Ягуар", "ЯГУАР", "ягуар"],
        "Jetour": ["JETOUR", "Jetour", "jetour", "Джетур", "ДЖЕТУР", "джетур"],
        "Jetta": ["JETTA", "Jetta", "jetta", "Джетта", "ДЖЕТТА", "джетта"],
        "Jishi": ["JISHI", "Jishi", "jishi", "Джиши", "ДЖИШИ", "джиши"],
        "Kia": ["KIA", "Kia", "kia", "Киа", "КИА", "киа"],
        "Land Rover": ["LAND ROVER", "LANDROVER", "Land Rover", "Landrover", "land rover", "landrover", "Ленд Ровер", "Ленд-Ровер", "ЛендРовер"],
        "Leamotor": ["LEAMOTOR", "Leamotor", "leamotor", "Лимото", "ЛИМОТО", "лимото"],
        "Lexus": ["LEXUS", "Lexus", "lexus", "Лексус", "ЛЕКСУС", "лексус"],
        "Lincoln": ["LINCOLN", "Lincoln", "lincoln", "Линкольн", "ЛИНКОЛЬН", "линкольн"],
        "LiXiang": ["LIXIANG", "LiXiang", "Li Auto", "LI AUTO", "lixiang", "ЛиСян", "ЛИ СЯН", "Ли Сян", "ли сян"],
        "Lotus": ["LOTUS", "Lotus", "lotus", "Лотус", "ЛОТУС", "лотус"],
        "Lynk & Co": ["LYNK & CO", "LYNKCO", "Lynk & Co", "LynkCo", "lynk & co", "lynkco", "Линк энд Ко", "ЛИНК ЭНД КО"],
        "Mazda": ["MAZDA", "Mazda", "mazda", "Мазда", "МАЗДА", "мазда"],
        "Mercedes-Benz": ["MERCEDES-BENZ", "Mercedes-Benz", "mercedes-benz", "MB", "mb", "Мерседес", "МЕРСЕДЕС", "мерседес", "Мерс", "МЕРС"],
        "MG": ["MG", "Mg", "mg", "ЭмДжи", "ЭМДЖИ", "эмджи", "Morris Garages", "MORRIS GARAGES"],
        "Mini": ["MINI", "Mini", "mini", "Мини", "МИНИ", "мини"],
        "Mitsubishi": ["MITSUBISHI", "Mitsubishi", "mitsubishi", "Митсубиси", "МИЦУБИСИ", "мицубиси"],
        "Neta": ["NETA", "Neta", "neta", "Нета", "НЕТА", "нета"],
        "Nio": ["NIO", "Nio", "nio", "Нио", "НИО", "нио"],
        "Nissan": ["NISSAN", "Nissan", "nissan", "Ниссан", "НИССАН", "ниссан"],
        "Peugeot": ["PEUGEOT", "Peugeot", "peugeot", "Пежо", "ПЕЖО", "пежо"],
        "Polestar": ["POLESTAR", "Polestar", "polestar", "Полстар", "ПОЛСТАР", "полстар"],
        "Porsche": ["PORSCHE", "Porsche", "porsche", "Порше", "ПОРШЕ", "порше"],
        "Skoda": ["SKODA", "Skoda", "skoda", "Шкода", "ШКОДА", "шкода"],
        "Smart": ["SMART", "Smart", "smart", "Смарт", "СМАРТ", "смарт"],
        "Tank": ["TANK", "Tank", "tank", "Танк", "ТАНК", "танк"],
        "Tesla": ["TESLA", "Tesla", "tesla", "Тесла", "ТЕСЛА", "тесла"],
        "Toyota": ["TOYOTA", "Toyota", "toyota", "Тойота", "ТОЙОТА", "тойота"],
        "Venucia": ["VENUCIA", "Venucia", "venucia", "Венуча", "ВЕНУЧА", "венуча"],
        "Volkswagen": ["VOLKSWAGEN", "Volkswagen", "volkswagen", "VW", "vw", "Фольксваген", "ФОЛЬКСВАГЕН", "фольксваген"],
        "Volvo": ["VOLVO", "Volvo", "volvo", "Вольво", "ВОЛЬВО", "вольво"],
        "Voyah": ["VOYAH", "Voyah", "voyah", "Воях", "ВОЯХ", "воях"],
        "Wuling": ["WULING", "Wuling", "wuling", "Улин", "УЛИН", "улин"],
        "Xiaomi": ["XIAOMI", "Xiaomi", "xiaomi", "Сяоми", "СЯОМИ", "сяоми"],
        "Xpeng": ["XPENG", "Xpeng", "xpeng", "Спен", "СПЕН", "спен"],
        "Zeekr": ["ZEEKR", "Zeekr", "zeekr", "Зикр", "ЗИКР", "зикр"],

        # Дополнительные бренды для России и Китая
        "Brilliance": ["BRILLIANCE", "Brilliance", "brilliance", "Бриллианс", "БРИЛЛИАНС"],
        "Datsun": ["DATSUN", "Datsun", "datsun", "Датсун", "ДАТСАН"],
        "Foton": ["FOTON", "Foton", "foton", "Фотон", "ФОТОН"],
        "Haima": ["HAIMA", "Haima", "haima", "Хайма", "ХАЙМА"],
        "Lifan": ["LIFAN", "Lifan", "lifan", "Лифан", "ЛИФАН"],
        "Ravon": ["RAVON", "Ravon", "ravon", "Равон", "РАВОН"],
        "Saipa": ["SAIPA", "Saipa", "saipa", "Саипа", "САИПА"],
        "Zotye": ["ZOTYE", "Zotye", "zotye", "Зоти", "ЗОТИ"]
    }

    for name, synonyms in brand_synonyms_data.items():
        brand = Brand.query.filter(Brand.name.ilike(name)).first()
        if not brand:
            brand = Brand(name=name, slug=name.lower().replace(" ", "-"))
            db.session.add(brand)
            db.session.flush()
            print(f"✅ Бренд создан: {brand.name}")

        for synonym in synonyms:
            exists = BrandSynonym.query.filter_by(name=synonym.lower()).first()
            if not exists:
                db.session.add(BrandSynonym(name=synonym.lower(), brand=brand))
                print(f"🔗 Добавлен синоним '{synonym}' → {brand.name}")

    db.session.commit()
    print("✅ Синонимы брендов добавлены.")
