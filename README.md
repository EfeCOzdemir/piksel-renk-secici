# Piksel Renk Seçici

Bir fotoğraf açıp üzerinde tıkladığınız pikselin renk kodunu **RGB** ve **HEX** olarak gösteren basit bir Windows masaüstü uygulaması.

## Özellikler

- PNG, JPG, BMP, GIF, WEBP, TIFF dosyalarını açar
- Tıklanan pikselin RGB, HEX ve (saydam görsellerde) alfa değerini gösterir
- İmlecin altındaki rengi canlı olarak gösterir
- Fare tekerleğiyle 40 kata kadar yakınlaştırma, sağ tıkla sürükleyerek kaydırma
- RGB veya HEX kodunu tek tıkla panoya kopyalama

## İndirme

**Python'a gerek olmadan:** [Releases](../../releases) bölümünden `RenkSecici.exe` dosyasını indirip çalıştırın.
Windows imzasız olduğu için SmartScreen uyarısı gösterebilir: "Ek bilgi → Yine de çalıştır".

**Python ile:**

```bash
pip install pillow
python renk_secici.py
```

Windows'ta `renk_secici.pyw` dosyasına çift tıklayarak konsol penceresi olmadan açabilirsiniz.

## Kullanım

| İşlem | Kısayol |
|---|---|
| Fotoğraf aç | `Ctrl+O` |
| Piksel seç | Sol tık |
| Yakınlaştır / uzaklaştır | Fare tekerleği |
| Kaydır | Sağ tık + sürükle |
| RGB kodunu kopyala | `Ctrl+C` |

## Exe'yi kendiniz derlemek

```bash
pip install pyinstaller pillow
python -m PyInstaller --onefile --windowed --name RenkSecici renk_secici.py
```
