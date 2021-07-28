import os
import sys, getopt
import re
from colorama import Fore, Back, Style

verbose = False
verboseLevel = 0
baseUrl = ''

##############################
# Input parameter processing #
##############################

def print_info(message):
    print("[INFO]: " + message)

def print_help():
    """Print help function to command line
    """
    print("USAGE: python main.py [options]")
    print("Options are: ")
    print("-h \t \t This help.")
    print("-url \t \t Base url of which to search for invalid links.")
    print("-l --language \t Check if language is consistent.")
    print("\t \t Format: xx. for subdomains or /xx/ for dir based language.")
    print("Examples: ")
    print("python main.py --url YOURWEBSITE.de -l /en/")

def set_language(language, url):
    """ Set language to url depending subdomain or dir method

    :language: Language to test 
    :url: base url  
    :returns: URL with language as subdomain or dir 

    """
    if language[0] == '/' and language[-1] == '/':
        # Dir based language selection
        return url + language
    elif language[-1] == '.':
        return language + url

def get_language_code(language):
    """Get language code from subdomain or dir format

    :language: TODO
    :returns: TODO

    """
    if language[0] == '/' and language[-1] == '/':
        return language[1:3]
    elif language[-1] == '.':
        return language[:-1]

def get_http_response_code(url):
    """ Get http return code
    url: Url to check http return code
    :returns: http code of given url 

    """
    command = "curl -Is " + url + " | head -1 | awk '{ print $2 }'"
    httpCode = os.popen(command).read()
    if verbose:
        print_info("HTTP code of " +  url + ": " + httpCode)
    return httpCode.strip()

def get_urls_in_response(url):
    """TODO: Download html code of given url and filter for valide urls
    :returns: List of urls contained in html response

    """
    command = "wget -qO- " + url
    rawHTML = os.popen(command).read()
    hrefRegexString = r"""href=".*?" """
    hrefs = re.findall(hrefRegexString, rawHTML)
    hrefs = re.findall('"([^"]*)"', str(hrefs))

    hrefRegexString = r"""href='.*?' """
    hrefs2 = re.findall(hrefRegexString, rawHTML)
    hrefs2 = re.findall("'([^']*)'", str(hrefs))

    hrefs += hrefs2

    for i in range(0, len(hrefs)):
        if hrefs[i][0] == "/":
            if baseUrl[-1] == "/":
                hrefs[i] = str(baseUrl[:-1]) + hrefs[i]
            else:
                hrefs[i] = str(baseUrl) + hrefs[i]

    command = "wget -qO- " + url + " | lynx -dump -listonly -stdin | grep -E 'http:|https:' | awk '{ $1=\"\"; print $0 }'"
    if verbose:
        print_info(command)
    htmlResponse = os.popen(command).read()
    if verbose:
        print_info(htmlResponse)
    return htmlResponse.splitlines() + hrefs

def linkcheck(urls, count=4, stack=[]):
    """Where the magic happens. Will preform everything to check all urls

    :urls: All urls  
    :returns: TODO

    """

    global baseUrl

    if verbose:
        print("Enter linkcheck")
    newUrls = ''

    if count > 0:
        if verboseLevel > 0:
            level = 4 - count
            print("\n--- Check urls (" + str(level) + "): ---")
            print(*urls, sep = "\n")
            print("\n")
        for url in urls:
            if verbose:
                print_info("linkcheck: " + str(count))
                print_info("Check: " + url)
            stack.append(url)
            httpResponse = get_http_response_code(url)        
            print("Response of " + url + " " + httpResponse)
            if verbose:
                print("Base: " + str(baseUrl) + " URL: " + url)
            if "200" in httpResponse:
                if str(baseUrlLang).strip() in url:
                    newUrls = get_urls_in_response(url)
                    linkcheck(newUrls, count-1, stack)
                else: 
                    if str(baseUrl).strip() in url:
                        print(Fore.YELLOW + "Language cahange")
                    else:
                        print(Fore.YELLOW + "Reached extern URL")
                    print("\n Stack: \n")
                    print(stack[-3:])
                    print("\n -- End of stack --")
                    print(Style.RESET_ALL)
            else: 
                print(Fore.RED + "HTTP response of " + url + ': ' + str(httpResponse))
                print(Style.RESET_ALL)
                if str(baseUrl).strip() in url:
                    print(Fore.YELLOW + "Language changed?")
                else:
                    print(Fore.YELLOW + "External URL reached")
                print("\n Stack: \n")
                print(stack[-3:])
                print("\n -- End of stack --")
                print(Style.RESET_ALL)
def main():

    # Main url to check
    url = '' 
    global baseUrl
    global baseUrlLang
    # Language code if provided
    languageCode = ''
    # Language like displayed in url
    languageType = ''
    global verbose

    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhp:t:l:s", ["verbose", "language=", "url=", "depth="])

    except getopt.GetoptError:
        # Print debug info
        print("Getopt Error")
        sys.exit(2)

    for option, argument in opts:
        if option in ("-h", "--help"):
            print_help()
            return 
        elif option in ("-url", "--url"):
            baseUrl = argument 
            # check if user has entered path with or without ending '/'
            if argument[-1] == "/":
                url = argument[:-1]
            else:
                url = argument
        elif option in ('-l', "--language"):
            url = set_language(argument, url)
            languageCode = get_language_code(argument)
            language = argument
        elif option in ('-v', "--verbose"):
            verbose = True 

    # Check if user has entered a url
    if url == '':
        print_info("Please enter valide url. \n done.")
        return 1
    
    baseUrlLang = url

    if verbose:
        print_info(url)
        print_info(languageCode)

    urls = []
    urls.append(url)

    stack = linkcheck(urls)
    print(stack)

if __name__ == "__main__":
    main()
