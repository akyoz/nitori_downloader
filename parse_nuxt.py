
from bs4 import BeautifulSoup
import re
import os

file_path = r'C:\Users\akyoz\.gemini\tmp\927be124b78ebb3e0e707780b5573dc6b61913030282ed3412d091c4aaf11a89\gallery_auth.html'
output_path = r'C:\Users\akyoz\.gemini\tmp\927be124b78ebb3e0e707780b5573dc6b61913030282ed3412d091c4aaf11a89\nuxt_data.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'lxml')
scripts = soup.find_all('script')

for script in scripts:
    if script.string and 'window.__NUXT__' in script.string:
        nuxt_data_str = script.string
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(nuxt_data_str)
        print(f"Nuxt data saved to {output_path}")
        break
else:
    print("Could not find window.__NUXT__ data in script tags.")
