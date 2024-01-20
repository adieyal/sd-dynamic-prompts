#if you install beautiful soup 4 the following script will download nai BUT you need to modify the rootdir var

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# pip install requests beautifulsoup4
rootdir = os.path.join('c:/','stablediffusion','extensions','sd-dynamic-prompts','wildcards','nae')

def download_links(url):
    # Make an HTTP request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links on the page
        links = soup.find_all('a')

        # Extract and print the href attribute of each link
        for link in links:
            href = link.get('href')

            # Make sure the href is not None and is a valid URL
            if href and href.startswith(('http://', 'https://')):
 
                if 'pastebin.com' in href:
                    text_before_url = link.previous.strip().replace(" -",'')
                    content = requests.get(href).content
                    soup2 = BeautifulSoup(content, 'html.parser')

                    first_h1 = soup2.find('h1')
                    if first_h1:
                        result = first_h1.text

                        print(result)
                        header = result
                    else:
                        print("no h1")

                    href = href.replace('pastebin.com/','pastebin.com/raw/')
                    # If you want to download the content of the link, you can use the requests library again
                    content = requests.get(href).content
                    #dl
                    destination = os.path.join(rootdir,header + '.txt')
                    # Save the content to a file or process it as needed
                    with open(destination, 'wb') as file:
                        file.write(content)
                elif 'rentry.org' in href:
                    text_before_url = link.previous.strip().replace(" -",'')
                    href = href + '/raw'
                    print(text_before_url)
                    content = requests.get(href).content
                    soup2 = BeautifulSoup(content, 'html.parser')
                    destination = os.path.join(rootdir,text_before_url + '.txt')
                    with open(destination, 'wb') as file:
                        file.write(content)
                else:
                    print(href + " is not a pastebin or rentry link")
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Example usage:
url_to_download = 'https://rentry.org/NAIwildcards'
download_links(url_to_download)
