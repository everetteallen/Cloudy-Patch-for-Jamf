

def CPJDownload_pubsub(event, context):
    # get libraries
    import base64
    from google.cloud import storage
    from urllib import request
    from urllib import parse
    from os.path import basename
    import os
    import json

    pubsub_message = base64.b64decode(event['data']).decode('utf-8')

    # setup a debug variable 
    bugged = 0

    if bugged:
        print(f'The message is --')
        print(pubsub_message)

    # unpack PatchTitle from message eventurally  Hard code for testing

    message_list = pubsub_message.split(",")
    patchName = message_list[0]
    patchVersion = message_list[1]
    if bugged:
        print(patchName)
    patchName = parse.quote(patchName)
    
    # Here we get our GSheet id and columns to use from the function runtime variables
    searchCol = os.environ.get('searchCol')    # usually A
    dataCol = os.environ.get('dataCol')    # usually B
    sheetID = os.environ.get('sheetID')

    # query the google sheet to get the url from the patch title  
    # Example: column A has patch title to lookup and column B has direct download URL for binary pkg file
    sheetLink = "https://docs.google.com/spreadsheets/d/" + sheetID + "/gviz/tq?tqx=out:csv&tq=select%20" + dataCol + "%20WHERE%20" + searchCol + "=%27" + patchName + "%27"
    if bugged:
        print (sheetLink)
    
    try:
        titlepkgDownload = request.urlopen(sheetLink).read().decode('utf-8').strip('\"')
    except:
        if bugged:
            errSheetlink = "ERROR - Can not get download link for Patch Title from sheet"
            print(errSheetlink)
        return("400")

    if not titlepkgDownload:
        if bugged:
            eer = "ERROR - No value for Package download URL"
            print(eer)
        return("400")
    else:
        print(titlepkgDownload)
    
    # set storage client
    client2 = storage.Client()

    # get bucket
    bucket_name = os.environ.get('bucketName')  # without gs://
    bucket = client2.get_bucket(bucket_name)  

    # get prefix
    try: 
        cpj_prefix = os.environ.get('pkgPrefix')
    except:
        cpj_preffix = 'NoPrefixError-'

    # set the list of urls
    # urls = ['https://download.mozilla.org/?product=firefox-pkg-latest-ssl&os=osx','https://dl.google.com/chrome/mac/stable/accept_tos%3Dhttps%253A%252F%252Fwww.google.com%252Fintl%252Fen_ph%252Fchrome%252Fterms%252F%26_and_accept_tos%3Dhttps%253A%252F%252Fpolicies.google.com%252Fterms/googlechrome.pkg','https://go.microsoft.com/fwlink/?linkid=525135']
    # urls = ['https://download.mozilla.org/?product=firefox-pkg-latest-ssl&os=osx']
    # url = 'https://dl.google.com/chrome/mac/stable/accept_tos%3Dhttps%253A%252F%252Fwww.google.com%252Fintl%252Fen_ph%252Fchrome%252Fterms%252F%26_and_accept_tos%3Dhttps%253A%252F%252Fpolicies.google.com%252Fterms/googlechrome.pkg'
    
    urls = [titlepkgDownload]

    for url in urls:
        try:
            remotefile = request.urlopen(url)
        except:
            if bugged:
                errLinkdownload = "ERROR - Can not get package from Patch Title Download URL"
                print(errLinkdownload)
            return("400")
            
        filename = basename(remotefile.url)
        filename = parse.unquote(filename)
        fname = cpj_prefix + filename
        blob = bucket.blob(fname)

        # See if file exists
        if blob.exists() == False:

            # copy file to google storage
            try:
                blob.upload_from_file(remotefile)
                print('copied file to google storage')

            # print error if file doesn't exists
            except:

                print('file does not exist')

        # print error if file already exists	in google storage
        else:
            print('file already exists in google storage')
# End CPJDownLoader