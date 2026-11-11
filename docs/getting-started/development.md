# Development Setup

Pixel Deck can be developed locally without a physical matrix by using the **Window renderer**.

## Clone and install

```bash
git clone https://github.com/petrsafrata/Pixel_Deck.git
cd Pixel_Deck
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure `config/config.yml`:

```yaml
app:
  render: "window"
```

Start Pixel Deck:

```bash
python main.py
```

The Window renderer simulates the 64×64 display and does not require Raspberry Pi hardware.

For Web Control Center development, see [Frontend Development](../developer-guide/frontend.md).
