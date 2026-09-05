PokéPack Opener V18

PRICING:
The website no longer checks prices live. It reads prices.json stored in the GitHub repository, so it loads much faster and works directly on GitHub Pages without a local server.

SETUP:
1. Upload/replace the contents of this folder in your GitHub repository root.
2. Commit the files.
3. In GitHub, open Actions -> Update card prices -> Run workflow once.
4. Wait for it to finish. It creates prices.json in the repository.
5. Refresh the website.

The workflow also runs daily at 21:30 UTC, after TCGCSV's normal daily update window.

Prices are TCGplayer market prices converted from USD to GBP at an approximate fixed rate of 0.74. They are indicative ungraded/raw values, not guaranteed UK sale prices.
