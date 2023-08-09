import csv
import os
import requests
import re

###############################################################################
# Najprej definirajmo nekaj pomožnih orodij za pridobivanje podatkov s spleta.
###############################################################################

# mapa, v katero bomo shranili podatke
foos_directory = 'foos'
# ime CSV datoteke v katero bomo shranili podatke
csv_filename = 'foos.csv'

def download_url_to_string(url):
    """Funkcija kot argument sprejme niz in poskusi vrniti vsebino te spletne
    strani kot niz. V primeru, da med izvajanje pride do napake vrne None.
    """
    try:
        # del kode, ki morda sproži napako
        headers = {'User-Agent': 'Chrome/111.0.5563.111'}
        page_content = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        # koda, ki se izvede pri napaki
        # dovolj je če izpišemo opozorilo in prekinemo izvajanje funkcije
        print('Spletna stran je trenutno nedosegljiva')
        return None
    # nadaljujemo s kodo če ni prišlo do napake
    return page_content.text


def save_string_to_file(text, directory, filename):
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko
    locirano v "directory"/"filename", ali povozi obstoječo. V primeru, da je
    niz "directory" prazen datoteko ustvari v trenutni mapi.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(text)
    return None


# Definirajte funkcijo, ki prenese glavno stran in jo shrani v datoteko.


def save_frontpage(page, directory, filename):
    """Funkcija shrani vsebino spletne strani na naslovu "page" v datoteko
    "directory"/"filename"."""
    text = download_url_to_string(page)
    save_string_to_file(text, directory, filename)


###############################################################################
# Po pridobitvi podatkov jih želimo obdelati.
###############################################################################


def read_file_to_string(directory, filename):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz."""
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as file_in:
        text = file_in.read()
    return text


# Definirajte funkcijo, ki sprejme niz, ki predstavlja vsebino spletne strani,
# in ga razdeli na dele, kjer vsak del predstavlja en turnir. To storite s
# pomočjo regularnih izrazov, ki označujejo začetek in konec posameznega
# oglasa. Funkcija naj vrne seznam nizov.


def page_to_tournaments(page_content):
    """Funkcija poišče posamezne turnirje, ki se nahajajo v spletni strani in
    vrne seznam turnirjev."""
    vzorec = r'<tr id="tnid\d+?" class=\'views-row .*?>.*?</tr>' 
    #'<article class="entity-body cf">.*?</article>'
    return re.findall(vzorec, page_content, flags = re.DOTALL)


# Definirajte funkcijo, ki sprejme niz, ki predstavlja turnir, in izlušči
# podatke o imenu, času in državi dogajanja rangu ter mizi.


def get_dict_from_tournament(block):
    """Funkcija iz niza za posamezen turnir izlušči podatke o imenu, času, državi, rangu
    in mizi ter vrne slovar, ki vsebuje ustrezne podatke."""
    ime = re.search(r'<td id="play_tour" style="cursor: default;">(.*)</td>', block)
    drzava = re.search(r'<td style="cursor: pointer;" onclick="window\.location =\'.*\'"><img src="\.\./members/flags/png/.*\.png"/><br>(.*)</td>', block)
    leto = re.search(r'<td><span.*</span></br>.*?(\d*)</td>', block)
    rang = re.search(r'<td align="center"><div class="category_tour" id="catour\d*">(.*?)</div>.*</td>', block).group(1)
    st_mize = re.search(r'<td id="img_tour".*><img src="/sites/default/files/images/ticons/(table_\d+).png"></td>', block).group(1)
#    cena = re.search(r'<strong class="price price--hrk">(.*) </strong>', block, flags=re.DOTALL)
    dictionary = {'table_16': 'Bonzini', 'table_17': 'Garlando', 'table_18': 'Roberto Sport', 'table_19': 'Rosengart', 
    'table_20': 'Topper', 'table_21': 'Tecball', 'table_22': 'Tornado', 'table_23': 'Multitable', 'table_25': 'Euro Soccer',
    'table_26': 'Undefined', 'table_27': 'Sardi', 'table_28': 'Leonhart', 'table_29': 'Fireball', 'table_81': 'Warrior',
    'table_104': 'Metegol Continental', 'table_116': 'Jupiter', 'table_117': 'Supra', 'table_127': 'Guardian', 'table_128': 'El Cotorro', 'table_129': 'Tecno', 'table_130': 'Ullrich Sport', 'table_131': 'Beast'}
    miza = dictionary[st_mize]
    minuli_rangi = {'InterCCup': 'ECL', 'ITSF Masters': 'World Cup', 'WCHs': 'World Cup'}
    if rang in minuli_rangi:
        rang = minuli_rangi[rang]
    return {'ime': ime.group(1), 'drzava': drzava.group(1), 'leto': leto.group(1), 'rang': rang, 'miza': miza}



# Definirajte funkcijo, ki sprejme ime in lokacijo datoteke, ki vsebuje
# besedilo spletne strani, in vrne seznam slovarjev, ki vsebujejo podatke o
# vseh oglasih strani.


def tournaments_from_file(filename, directory):
    """Funkcija prebere podatke v datoteki "directory"/"filename" in jih
    pretvori (razčleni) v pripadajoč seznam slovarjev za vsak oglas posebej."""
    text = read_file_to_string(directory, filename)
    blocks = page_to_tournaments(text)
    tournaments = [get_dict_from_tournament(block) for block in blocks]
    return [tournament for tournament in tournaments if tournament != None]


###############################################################################
# Obdelane podatke želimo sedaj shraniti.
###############################################################################


def write_csv(fieldnames, rows, directory, filename):
    """
    Funkcija v csv datoteko podano s parametroma "directory"/"filename" zapiše
    vrednosti v parametru "rows" pripadajoče ključem podanim v "fieldnames"
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return


# Definirajte funkcijo, ki sprejme neprazen seznam slovarjev, ki predstavljajo
# podatke iz oglasa mačke, in zapiše vse podatke v csv datoteko. Imena za
# stolpce [fieldnames] pridobite iz slovarjev.


def write_ctournaments_to_csv(tournaments, directory, filename):
    """Funkcija vse podatke iz parametra "tournaments" zapiše v csv datoteko podano s
    parametroma "directory"/"filename". Funkcija predpostavi, da so ključi vseh
    slovarjev parametra tournaments enaki in je seznam tournaments neprazen."""
    # Stavek assert preveri da zahteva velja
    # Če drži se program normalno izvaja, drugače pa sproži napako
    # Prednost je v tem, da ga lahko pod določenimi pogoji izklopimo v
    # produkcijskem okolju
    ##assert tournaments and (all(j.keys() == tournaments[0].keys() for j in tournaments))
    write_csv(tournaments[0].keys(), tournaments, directory, filename)


# Celoten program poženemo v glavni funkciji

def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Oglase prenese iz bolhe
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """

    if redownload:
        for leto in range(2004, 2024):        
            # definirajte URL glavne strani turnirjev v organizaciji ITSF
            foos_frontpage_url = f'https://www.tablesoccer.org/tournaments?sort_by=field_date_value&sort_order=ASC&field_tour_value={leto}'
            
            # ime datoteke v katero bomo shranili glavno stran
            frontpage_filename = f'itsf_{leto}.html'
            

    # Najprej v lokalno datoteko shranimo glavno stran
            save_frontpage(foos_frontpage_url, foos_directory, frontpage_filename)
    if reparse:
    # Iz lokalne (html) datoteke preberemo podatke
    # Podatke preberemo v lepšo obliko (seznam slovarjev)
        alltournaments = []
        for leto in range(2004,2024):
            frontpage_filename = f'itsf_{leto}.html'
            tournamentss = tournaments_from_file(frontpage_filename, foos_directory)
            alltournaments.extend(tournamentss)
    # Podatke shranimo v csv datoteko
        write_ctournaments_to_csv(alltournaments, foos_directory, csv_filename)
    # Dodatno: S pomočjo parametrov funkcije main omogoči nadzor, ali se
    # celotna spletna stran ob vsakem zagon prenese (četudi že obstaja)
    # in enako za pretvorbo

    


if __name__ == '__main__':
    main(False)