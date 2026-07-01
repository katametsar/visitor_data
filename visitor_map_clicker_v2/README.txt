Kasutamine
==========

Kaustas peavad olema:
- map_clicker.html
- museum_map.png
- t_codes.csv

Käivita Terminalis:

cd ~/Desktop/visitor-logs
python3 -m http.server 8000

Ava brauseris:

http://localhost:8000/map_clicker.html

Töövoog:
1. Vali vasakult T-kood või kasuta nuppu "Järgmine tühi".
2. Kliki kaardil sobivasse kohta.
3. Punkt salvestub brauseri localStorage'i automaatselt.
4. Sama T-koodi uuesti paigutades vana punkt asendatakse.
5. Punkti saab lohistada või popupist kustutada.
6. Lõpus vajuta "Salvesta coordinates.csv".

Kui oled juba varem coordinates.csv salvestanud, saad selle nupuga "Impordi olemasolev coordinates.csv" tagasi laadida.
