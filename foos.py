import csv
import os
import requests
import re

###############################################################################
# Najprej definirajmo nekaj pomožnih orodij za pridobivanje podatkov s spleta.
###############################################################################

# definirajte URL glavne strani bolhe za oglase z mačkami
foos_frontpage_url = 'https://www.tablesoccer.org/tournaments'
# mapa, v katero bomo shranili podatke
foos_directory = 'foos'
# ime datoteke v katero bomo shranili glavno stran
frontpage_filename = 'itsf_2023.html'
# ime CSV datoteke v katero bomo shranili podatke
csv_filename = 'foos23.csv'


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
# in ga razdeli na dele, kjer vsak del predstavlja en oglas. To storite s
# pomočjo regularnih izrazov, ki označujejo začetek in konec posameznega
# oglasa. Funkcija naj vrne seznam nizov.


def page_to_tournaments(page_content):
    """Funkcija poišče posamezne turnirje, ki se nahajajo v spletni strani in
    vrne seznam turnirjev."""
    vzorec = r'<tr id="tnid\d+" class='views-row views-row-\d+ views-row-even notpassed  livenow '>' # problemi z narekovaji
    '<article class="entity-body cf">.*?</article>'
    return re.findall(vzorec, page_content, flags = re.DOTALL)


# Definirajte funkcijo, ki sprejme niz, ki predstavlja turnir, in izlušči
# podatke o imenu, lokaciji, datumu objave in ceni v oglasu.


def get_dict_from_ad_block(block):
    """Funkcija iz niza za posamezen oglasni blok izlušči podatke o imenu, ceni
    in opisu ter vrne slovar, ki vsebuje ustrezne podatke."""
    ime = re.search(r'<h3 .*"><a .*>(.*)</a></h3>', block)
    lokacija = re.search(r'Lokacija: </span>(.*)<br />', block)
    datum = re.search(r'<time .*>(.*).</time>', block)
    cena = re.search(r'<strong class="price price--hrk">(.*) </strong>', block, flags=re.DOTALL)
    if ime == None or lokacija == None or datum == None or cena == None:
        return None
    elif 'Cena po dogovoru' in cena.group(1):
        cena = 'Cena po dogovoru'
    else:
        cena = re.search(r'(\d+)&nbsp;<span class="currency">(.+)</span>', cena.group(1))
        cena = cena.group(1) + ' ' + cena.group(2)
    return {'ime': ime.group(1), 'lokacija': lokacija.group(1), 'datum': datum.group(1), 'cena': cena}



# Definirajte funkcijo, ki sprejme ime in lokacijo datoteke, ki vsebuje
# besedilo spletne strani, in vrne seznam slovarjev, ki vsebujejo podatke o
# vseh oglasih strani.


def ads_from_file(filename, directory):
    """Funkcija prebere podatke v datoteki "directory"/"filename" in jih
    pretvori (razčleni) v pripadajoč seznam slovarjev za vsak oglas posebej."""
    text = read_file_to_string(directory, filename)
    blocks = page_to_ads(text)
    ads = [get_dict_from_ad_block(block) for block in blocks]
    return [ad for ad in ads if ad != None]


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


def write_ctournaments_to_csv(ads, directory, filename):
    """Funkcija vse podatke iz parametra "ads" zapiše v csv datoteko podano s
    parametroma "directory"/"filename". Funkcija predpostavi, da so ključi vseh
    slovarjev parametra ads enaki in je seznam ads neprazen."""
    # Stavek assert preveri da zahteva velja
    # Če drži se program normalno izvaja, drugače pa sproži napako
    # Prednost je v tem, da ga lahko pod določenimi pogoji izklopimo v
    # produkcijskem okolju
    assert ads and (all(j.keys() == ads[0].keys() for j in ads))
    write_csv(ads[0].keys(), ads, directory, filename)


# Celoten program poženemo v glavni funkciji

def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Oglase prenese iz bolhe
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """

    if redownload:
    # Najprej v lokalno datoteko shranimo glavno stran
        save_frontpage(foos_frontpage_url, foos_directory, frontpage_filename)
    if reparse:
    # Iz lokalne (html) datoteke preberemo podatke
    # Podatke preberemo v lepšo obliko (seznam slovarjev)
        tournaments = ads_from_file(frontpage_filename, foos_directory)
    # Podatke shranimo v csv datoteko
        write_ctournaments_to_csv(tournaments, foos_directory, csv_filename)
    # Dodatno: S pomočjo parametrov funkcije main omogoči nadzor, ali se
    # celotna spletna stran ob vsakem zagon prenese (četudi že obstaja)
    # in enako za pretvorbo

    


if __name__ == '__main__':
    main(False)