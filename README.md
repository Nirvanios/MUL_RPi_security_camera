# MUL - smartcamera
Jedná se o aplikaci schopnou detekovat osoby v prostrou snímaném kamerou. 
Informace o pohybu pak ukládá ve formě videa na vzdálený server a notifikuje užiovatele pomcí emailu.
Celý projekt je navržen tak aby běžel na platformě Rapberry Pi společně s kamerou připojenou přes CSI. 


 
## Použití
#### smartcamera
Spuštění

    python3 ./smartcamera.py [--config]

Parametr `--config` zobrazí aktuální konfiguraci openCV parametrů pro detekci osob. Je zobrazeno několik oken, 
proto je nutné mít připojen diplay, případně být připojen přes vzdálenou plochu.
Celkově se chod programu nastavuje pomocí konfiguračního souboru `config.json`.
Pomocí něj lze pak nakonfigurovat e-mail pro notifikace, adresu file serveru a openCV parametry pro úpravu detekci osob.


#### File server
Spuštění

    python3 ./Server.py --ip <ip adresa> --port <port> [--dir <output_dir>]

Pokud není specifikován parametr `--dir` jsou soubory standardně ukládány do složky `/home/pi/imgae_server/`