# Created by 2481632 / marvin

import os
import sys, getopt
import re
import unicodedata
from colorama import Fore, Back, Style
import subprocess
from enum import Enum

verbose = False
verboseLevel = 0
baseUrl = ''
printValide = False 

class urlCode(Enum):
    OK = 0,
    LAN = 1

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
    print("--url \t \t Base url of which to search for invalid links.")
    print("--language \t Check if language is consistent.")
    print("\t \t Format: xx. for subdomains or /xx/ for dir based language.")
    print("-d \t \t Depth of recursions (default: 3)")
    print("--printvalide \t Print all successfully (HTTP code 200, 301) tested links")
    print("-v \t \t verbose mode")
    print("\nExamples: ")
    print("Check Links on YOURWEBSITE.EU 3 levels deep.")
    print("This will warn you if you have broken links or you link to pages on your own site which changes the language.")
    print("\t python main.py --url YOURWEBSITE.EU --language /en/")

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
    # command = "curl -Is " + url + " | head -1 | awk '{ print $2 }'"
    command = "curl -s -o /dev/null -I -w '%{http_code}' '{url}'"
    command = command.replace("{url}", url).lstrip()
    httpCode = os.popen(command).read()
    if verboseLevel > 2:
        print_info(command)
        print_info("HTTP code of " +  url + ": " + httpCode)
    return httpCode.strip()

def get_urls_in_response(url):
    """Download html code of given url and filter for valide urls
    :returns: List of urls contained in html response

    """
    command = "lynx -dump -listonly '{url}' | grep -E '^[[:space:]]*[0-9]*.[[:space:]]*(https://|http://)' | awk '{ $1=\"\"; print $0 }'"

    command = command.replace("{url}", url)

    # Execute bash command and save stdot
    htmlResponse = os.popen(command).read()

    # Output of bash was in one line with whitespaces as 
    # delimiter. Split line at whitespace.
    newUrls = htmlResponse.splitlines()

    if verbose:
        print("\nHTML Response:  \n")
        print(htmlResponse)

    # Remove whitespaces on every single string
    return [s.lstrip() for s in newUrls]

def print_stack(stack):
    """Print stack in list

    :stack: List of urls which has been visited

    """
    print("\n-- Begin of stack --\n")
    for item in stack:
        print("-> " + str(item))
    print("\n-- End of stack --\n")

def validate_url(url, stack=None):
    """Check http status code, language change etc. 

    :url: URL to check 
    :returns:
        http code, code

    """

    # ToDo: Return reason why not valid #

    # We want to return not true if we hit an unkown or wrong url, even if the url is valid.
    # ToDo: Make it possible to check external pages as well.
    retFalse = False

    # Check http code of url
    httpResponse = get_http_response_code(url)

    # All http response codes which should be accepted
    allowedResponses = ["200", "301", "302"]
    # Response codes which indecate more or less serious problems
    criticalResponses = ["500", "404"]

    # Check if if base url has changed
    if (str(url).find(str(baseUrlLang)) == -1):
        # Check if we are still on our page but language has changed
        if (str(url).find(str(baseUrl)) == -1):
            print(Fore.CYAN + "\n-> Reached external link\n" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "\n-> Language changed?\n" + Style.RESET_ALL)
        retFalse = True

    # Check if http response code of url is not ok
    if (str(httpResponse) in allowedResponses) and not retFalse:
        if printValide or verbose:
            print("HTTP Response of: {url} {httpResponse} OK".format(url=url, httpResponse=httpResponse))
        return True, httpResponse 

    if httpResponse in criticalResponses:
        print(Fore.RED, end="")
    print("HTTP Rresponse of: {url} : {httpCode}".format(url=url, httpCode=httpResponse) + Style.RESET_ALL)
    if stack!= None:
        print_stack(stack)
    return False, httpResponse

def linkcheck(urls, depth=3, stack=[], checkedUrls=None):
    """Where the magic happens. Will preform everything to check all urls

    :urls: All urls  
    :returns: List of all checked links.

    """

    global baseUrl

    # Initialize list / first time call
    if checkedUrls == None:
        checkedUrls = []

    newUrls = ''

    if verbose:
        print("Check {num} urls: ".format(num=len(urls)))
        print_stack(stack)

    for url in urls:

        #if len(stack) > 0:
        #    print("Check in: {}".format(stack[-1]))

        # Check if url has already been tested
        checkedUrl = [x for x in checkedUrls if x[0] == url and x[1] >= depth]
        if len(checkedUrl) > 0:
            if verbose:
                print("Already checked in depth: {checkedDepth}/{currentDepth}: {url}".replace("{url}", url).replace("{checkedDepth}", str(checkedUrl[0][1])).replace("{currentDepth}", str(depth)))
            continue

        # Add url to checked urls
        checkedUrls.append([url, depth])

        # If url is not valid (404)
        valid, httpCode = validate_url(url, stack)
        if not valid:
            continue 

        # Check if we followd max depth links and
        # do not check links on current url
        if depth < 1:
            continue 

        # Get all urls on page at url 
        newUrls = get_urls_in_response(url)

        # Check if page at url has more links to follow.
        if len(newUrls) <= 0:
            continue

        # Add current url to stack
        stack.append(url)

        if verbose:
            print("Current Stack: ")
            print_stack(stack)
    
        # Call linkcheck with new urls
        linkcheck(newUrls, depth - 1, stack[:], checkedUrls) 
        
        # Remove current url from stack so we can add the next
        stack.pop()

    return checkedUrls

def main():
    """Main Function"""
    # Main url to check
    url = '' 
    # How many itterations should we do
    depth = 3
    # Language code if provided
    languageCode = ''
    # Language like displayed in url
    languageType = ''

    global baseUrl
    global baseUrlLang
    global verbose
    global printValide 

    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhpd:t:l", ["verbose", "printvalide", "language=", "url=", "depth="])

    except getopt.GetoptError:
        # Print debug info
        print("Getopt Error")
        sys.exit(2)

    # Handle user input
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
        elif option in ('-d', "--depth"):
            try: 
                depth = int(argument)
            except: 
                print("Please enter an integer")
                exit()
        elif option in ('-v', "--verbose"):
            verbose = True 
        elif option in ("--printvalide"):
            printValide = True 

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

    checkedUrls = linkcheck(urls, depth=depth)
    
    print("\n -- Checked Urls: --")

    print("Count: {countOfUrls}".format(countOfUrls=len(checkedUrls)))

if __name__ == "__main__":
    main()
