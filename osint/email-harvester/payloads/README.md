# Email Harvester Payloads & Dorks

This folder contains lists of search dorks, regular expressions, and payload patterns to enhance the email harvesting process.

## Advanced Search Engine Dorks

When extending the `search_engines.py` module to target platforms like Google or Bing, you can use these advanced dorks to find exposed emails:

### Google / Bing Dorks
- `site:target.com intext:"@target.com"`
- `site:linkedin.com/in "*@target.com"`
- `site:pastebin.com "@target.com"`
- `filetype:pdf intext:"@target.com"`
- `filetype:xls OR filetype:xlsx intext:"@target.com"`
- `intitle:"index of" "contacts.txt"`

### GitHub Dorks (Requires API)
- `"@target.com" filename:users`
- `"@target.com" filename:config`
- `"@target.com" extension:sql`
